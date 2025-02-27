from datetime import datetime
from typing import List, Optional, Tuple, Dict
import pickle
import sys
import os

# add base folder (OPENTGPTPU) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dataclasses import dataclass
from enum import Enum
import argparse
import config
from generate import make_hostmem, make_weights
from assembler import assemble
from runtpu import runtpu, print_mem


class Operation(Enum):
    RHM = "RHM"
    WHM = "WHM"
    RW = "RW"
    MMC = "MMC"
    ACT = "ACT"
    NOP = "NOP"
    SYNC = "SYNC"
    HLT = "HLT"


instr_to_arg_count = {
    Operation.RHM: 3,
    Operation.WHM: 3,
    Operation.RW: 1,
    Operation.MMC: 3,
    Operation.ACT: 3,
    Operation.NOP: 0,
    Operation.SYNC: 0,
    Operation.HLT: 0
}


class Opflag(Enum):
    OVERWRITE = "O"
    SWITCH = "S"
    RELU = "R"
    SIGMOID = "Q"


class ProgramType(Enum):
    Test = "test"
    Control = "control"
    NoNop = "nonop"


@dataclass
class Instruction:
    operation: Operation
    matsize: int
    absolute_addrs: bool
    opflag: Optional[Opflag] = None
    arg1: Optional[int] = None
    arg2: Optional[int] = None
    arg3: Optional[float] = None

    # if absolute addresses is true, then UB and HM addresses are taken literally
    # otherwise, they are taken as relative to matsize. For example, if matsize is 16,
    # then address 1 will be converted to UB address 16, since 16 is the start of slot 1.
    # this allows for testing with different matsizes without changing the provided instructions.
    def __init__(self, instr: str, matsize: int, absolute_addrs: bool) -> 'Instruction':
        self.matsize = matsize
        self.absolute_addrs = absolute_addrs

        # split the instruction into operation and arguments
        split = instr.split(' ')
        if len(split) == 0 or len(split) > 4:
            raise ValueError(f"Invalid instruction: {instr}")
        
        # add the opflag and remove it from the operation field if it exists
        if split[0][-2] == '.' and split[0][-1] in [flag.value for flag in Opflag]:
            self.opflag = Opflag(split[0][-1])
            split[0] = split[0][:-2]

        # add the operation
        try:
            self.operation = Operation(split[0])
        except KeyError:
            raise ValueError(f"Invalid instruction: {split[0]}")
        
        # check for correct argcount
        if len(split) - 1 != instr_to_arg_count[self.operation]:
            raise ValueError(f"Invalid arg count: {instr}")

        # assign args
        for i in range(1, len(split)):
            setattr(self, f"arg{i}", split[i])

    # turn the Instruction object into a string
    def to_string(self) -> str:
        instruction_str = self.operation.value
        if self.opflag:
            instruction_str += f".{self.opflag.value}"

        if self.operation in [Operation.RHM, Operation.WHM, Operation.MMC, Operation.ACT]:
            if self.absolute_addrs:
                instruction_str += f" {int(self.arg1)}, {int(self.arg2)}, {int(float(self.arg3))}"
            else:
                instruction_str += f" {int(self.arg1) * self.matsize}, {int(self.arg2) * self.matsize}, {int(float(self.arg3) * self.matsize)}"
        elif self.operation in [Operation.RW]:
            instruction_str += f" {self.arg1}"
        
        return instruction_str     


@dataclass
class Program:
    instrs: List[Instruction]
    setup: List[Instruction]
    cleanup: List[Instruction]
    distance: int
    bitwidth: int
    matsize: int
    name: str
    reset: bool
    program_dir: str
    absolute_addresses: bool
    ctrl_distance: int

    # parse instrs, setup, and cleanup into Instruction objects
    # load the rest of the args into the Program object
    def __init__(self, instrs, setup, cleanup, distance, bitwidth, matsize, name, reset, absoluteaddrs, program_dir: str, ctrl_distance: int) -> 'Program':
        self.instrs = []
        self.setup = []
        self.cleanup = []
        self.ctrl_distance = ctrl_distance

        for i in range(len(instrs)):
            self.instrs.append(Instruction(instrs[i], matsize, absoluteaddrs))

        if setup:
            for i in range(len(setup)):
                self.setup.append(Instruction(setup[i], matsize, absoluteaddrs))

        if cleanup:
            for i in range(len(cleanup)):
                self.cleanup.append(Instruction(cleanup[i], matsize, absoluteaddrs))

        self.distance = distance
        self.bitwidth = bitwidth
        self.matsize = matsize
        self.name = name
        self.reset = reset
        self.program_dir = program_dir
        self.absolute_addresses = absoluteaddrs

    def get_filepath(self, binary: bool, ptype: ProgramType) -> str:
        filepath = self.program_dir

        if ptype == ProgramType.Control:
            filepath += f"/control_{self.matsize}m"
        elif ptype == ProgramType.NoNop:
            filepath += f"/nonop_{self.matsize}m"
        elif ptype == ProgramType.Test:
            filepath += f"/test_{self.matsize}m_{self.distance}d"

        if binary:
            return f"{filepath}.out"
        else:
            return f"{filepath}.a"
    
    # make a .a file for the program at the right location
    def generate_dot_a(self, ptype: ProgramType) -> None:
        filepath = self.get_filepath(False, ptype)
        nop = Instruction("NOP", self.matsize, self.absolute_addresses)
        hlt = Instruction("HLT", self.matsize, self.absolute_addresses)

        with open(filepath, "w") as f:

            # all generated files should start with ctrl_distance NOPs
            # (PC 0 through PC ctrl_distance - 1)
            if ptype != ProgramType.NoNop:
                for _ in range(self.ctrl_distance):
                    f.write(f"{nop.to_string()}\n")
            
            # after that, every ctrl_distance instructions is a setup instr
            for i in range(len(self.setup)):
                f.write(f"{self.setup[i].to_string()}\n")
                if ptype != ProgramType.NoNop:
                    for _ in range(self.ctrl_distance - 1):
                        f.write(f"{nop.to_string()}\n")

            # then the instructions under test, self.distance instructions apart
            if len(self.instrs) != 2:
                raise ValueError("Please provide exactly two instructions to test.")
            f.write(f"{self.instrs[0].to_string()}\n")
            if ptype != ProgramType.NoNop:
                for _ in range(self.distance - 1):
                    f.write(f"{nop.to_string()}\n")
            f.write(f"{self.instrs[1].to_string()}\n")

            # pad with NOPs so that the first cleanup instruction is 
            # 2*ctrl_distance lines after the first instruction under test 
            if ptype != ProgramType.NoNop:
                for _ in range(2*self.ctrl_distance - self.distance - 1):
                    f.write(f"{nop.to_string()}\n")

            # after that, every ctrl_distance instructions is a cleanup instr
            for i in range(len(self.cleanup)):
                f.write(f"{self.cleanup[i].to_string()}\n")
                if ptype != ProgramType.NoNop:
                    for _ in range(self.ctrl_distance - 1):
                        f.write(f"{nop.to_string()}\n")

            # finally, HLT
            f.write(f"{hlt.to_string()}\n")


# run the squish test given the args
def squish_test(instrs: list, distance: int, bitwidth: int, matsize: int, 
                name: str, setup: list, cleanup: list, reset: bool, 
                absoluteaddrs: bool, test_folder: str, ctrl_distance: int,
                use_nops: bool = True) -> Tuple[bool, Dict[int, int]]:

    config.MATSIZE = matsize
    config.DWIDTH = bitwidth

    if len(instrs) != 2:
        print("Please provide two instructions to test.")
        exit(1)

    if distance < 1 or distance > ctrl_distance:
        print(f"Distance must be between 1 and {ctrl_distance}.")
        exit(1)

    # parse args into Program object
    program_dir = f"{os.path.dirname(__file__)}/{test_folder}/{name}"
    program = Program(instrs, setup, cleanup, distance, bitwidth, matsize, name,
                      reset, absoluteaddrs, program_dir, ctrl_distance) 

    # make folder for the test (squish/name/) and add weights and inputs if they
    # don't already exist
    weights_filename = make_weights(program_dir, program.matsize, 
                                    program.bitwidth, num_weights=8)
    hostmem_filename = make_hostmem(program_dir, program.matsize, 
                                    program.bitwidth, num_tiles=8)

    test_type = ProgramType.Test if use_nops else ProgramType.NoNop

    # if -r is set, or the following don't exist, or the test name is default (test):
    # generate .a file for d=ctrl_distance (control)
    if reset or not os.path.exists(program.get_filepath(binary=False, ptype=ProgramType.Control)) or program.name == "test":
        program.generate_dot_a(ProgramType.Control)

    # assemble into .out file for d=ctrl_distance (control)
    if reset or not os.path.exists(program.get_filepath(binary=True, ptype=ProgramType.Control)) or program.name == "test":
        assemble(program.get_filepath(binary=False, ptype=ProgramType.Control), 0)

    # generate .a file for the apropriate distance (distance test) or without nops
    if reset or not os.path.exists(program.get_filepath(binary=False, ptype=test_type)) or program.name == "test":
        program.generate_dot_a(test_type)

    # assemble into .out file (distance test or without nops)
    if reset or not os.path.exists(program.get_filepath(binary=True, ptype=test_type)) or program.name == "test":
        assemble(program.get_filepath(binary=False, ptype=test_type), 0)

    # run d=ctrl_distance .out file (control) and get the resulting matrix and 
    # final trace
    print(f"Running {name} for d = {distance}. b = {bitwidth}, m = {matsize}")
    print(f"Control")
    ctrl_output_folderpath = f"{program_dir}/ctrl_{config.DWIDTH}b_{config.MATSIZE}m"
    if reset or not os.path.exists(ctrl_output_folderpath) or program.name == "test":
        runtpu_ctrl_args = argparse.Namespace(prog=program.get_filepath(binary=True, ptype=ProgramType.Control), 
                                              hostmem=hostmem_filename, 
                                              weightsmem=weights_filename)
        # ctrl_hostmem, ctrl_ubuffer, ctrl_acc_mems, ctrl_wbufs \
        ctrl_hostmem \
            = runtpu(runtpu_ctrl_args, output_folder_path=ctrl_output_folderpath)
    else:
        with open(os.path.join(ctrl_output_folderpath, "hostmem.pkl"), "rb") as f:
            ctrl_hostmem = pickle.load(f)
        # with open(os.path.join(ctrl_output_folderpath, "ubuffer.pkl"), "rb") as f:
        #     ctrl_ubuffer = pickle.load(f)
        # with open(os.path.join(ctrl_output_folderpath, "accmems.pkl"), "rb") as f:
        #     ctrl_acc_mems = pickle.load(f)
        # with open(os.path.join(ctrl_output_folderpath, "wqueue.pkl"), "rb") as f:
        #     ctrl_wbufs = pickle.load(f)

    # run runtpu.py in standard mode and get result
    print(f"Test")
    if test_type == ProgramType.NoNop:
        test_output_folderpath = f'{program_dir}/nonop_{config.DWIDTH}b_{config.MATSIZE}m'
    else:
        test_output_folderpath = f'{program_dir}/test_{config.DWIDTH}b_{config.MATSIZE}m_{distance}d'
    if reset or not os.path.exists(test_output_folderpath) or program.name == "test":
        runtpu_test_args = argparse.Namespace(prog=program.get_filepath(binary=True, ptype=test_type), 
                                              hostmem=hostmem_filename, 
                                              weightsmem=weights_filename)
        # test_hostmem, test_ubuffer, test_acc_mems, test_wbufs \
        test_hostmem \
            = runtpu(runtpu_test_args, output_folder_path=test_output_folderpath)
    else:
        with open(os.path.join(test_output_folderpath, "hostmem.pkl"), "rb") as f:
            test_hostmem = pickle.load(f)
        # with open(os.path.join(test_output_folderpath, "ubuffer.pkl"), "rb") as f:
        #     test_ubuffer = pickle.load(f)
        # with open(os.path.join(test_output_folderpath, "accmems.pkl"), "rb") as f:
        #     test_acc_mems = pickle.load(f)
        # with open(os.path.join(test_output_folderpath, "wqueue.pkl"), "rb") as f:
        #     test_wbufs = pickle.load(f)

    # compare results and output a verdict
    # comparison may include a diff (between control and test) of host memory as ndarray and trace at last cycle
    # let's just do a comparison of the host memory for now
    # print("Control host memory:")
    # print_mem(ctrl_hostmem)
    # print("Test host memory:")
    # print_mem(test_hostmem)

    passed = True

    if ctrl_hostmem != test_hostmem:
        print("Test failed (hostmem)")
        print("Control host memory:")
        print_mem(ctrl_hostmem)
        print("Test host memory:")
        print_mem(test_hostmem)
        passed = False

    # if ctrl_ubuffer != test_ubuffer:
    #     print("Test failed (ubuffer)")
    #     print("Control ubuffer:")
    #     print(ctrl_ubuffer)
    #     print("Test ubuffer:")
    #     print(test_ubuffer)
    #     passed = False

    # if ctrl_acc_mems != test_acc_mems:
    #     print("Test failed (accmems)")
    #     print("Control accmems:")
    #     print(ctrl_acc_mems)
    #     print("Test accmems:")
    #     print(test_acc_mems)
    #     passed = False

    # if ctrl_wbufs != test_wbufs:
    #     print("Test failed (wbufs)")
    #     print("Control wbufs:")
    #     print(ctrl_wbufs)
    #     print("Test wbufs:")
    #     print(test_wbufs)
    #     passed = False

    return passed


# invoke squish test from command line
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate test cases that squish TPU instructions together.')
    parser.add_argument("instrs", nargs=2, help="Instructions under test.")
    parser.add_argument("-d", "--distance", type=int, default=50, help="Distance between instructions under test.")
    parser.add_argument("-b", "--bitwidth", type=int, default=32, help="Bitwidth of the instructions.")
    parser.add_argument("-m", "--matsize", type=int, default=8, help="Size of the matrices.")
    parser.add_argument("-n", "--name", type=str, default="test", help="Name of the test.")
    parser.add_argument("-s", "--setup", type=str, action="append", help="Setup instructions.")
    parser.add_argument("-c", "--cleanup", type=str, action="append", help="Cleanup instructions.")
    parser.add_argument("-r", "--reset", action="store_true", help="Rebuild test folder from the beginning.")
    parser.add_argument("-a", "--absoluteaddrs", action="store_true", help="Use absolute addresses.")
    parser.add_argument("-t", "--test_folder", type=str, default="default_test", help="Folder to store the test(s).")
    parser.add_argument("--ctrl_distance", type=int, default=50, help="Distance between instructions in the control.")
    args = parser.parse_args()

    instrs: list = args.instrs
    distance: int = args.distance
    bitwidth: int = args.bitwidth
    matsize: int = args.matsize
    name: str = args.name
    setup: list = args.setup if args.setup else []
    cleanup: list = args.cleanup if args.cleanup else []
    reset: bool = args.reset
    absoluteaddrs: bool = args.absoluteaddrs
    test_folder: str = args.test_folder
    ctrl_distance: int = args.ctrl_distance

    squish_test(instrs, distance, bitwidth, matsize, name, 
                setup, cleanup, reset, absoluteaddrs, test_folder, 
                ctrl_distance)
