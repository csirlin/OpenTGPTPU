"""
parameters for:
- instruction under test 1
- instruction under test 2
- distance between instructions under test (1-50)
- bitwidth
- matsize
- test name
- setup instructions
- cleanup instructions
"""

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

@dataclass
class Instruction:
    operation: Operation
    opflag: Optional[Opflag] = None
    arg1: Optional[int] = None
    arg2: Optional[int] = None
    arg3: Optional[int] = None

    def __init__(self, instr: str) -> 'Instruction':
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
            setattr(self, f"arg{i}", int(split[i]))

    # turn the Instruction object into a string
    # if absolute addresses is true, then UB and HM addresses are taken literally
    # otherwise, they are taken as relative to matsize. For example, if matsize is 16,
    # then address 1 will be converted to UB address 16, since 16 is the start of slot 1.
    # this allows for testing with different matsizes without changing the provided instructions.
    # absolute addressing is still allowed to enable future work to determine how far you can
    # compress partial-length instrs, like a matmul of only 4 rows with a matsize of 8.
    def to_string(self, matsize: int, absolute_addresses: bool) -> str:
        instruction_str = self.operation.value
        if self.opflag:
            instruction_str += f".{self.opflag.value}"

        if self.operation in [Operation.RHM, Operation.WHM, Operation.MMC, Operation.ACT]:
            if absolute_addresses:
                instruction_str += f" {self.arg1}, {self.arg2}, {self.arg3}"
            else:
                instruction_str += f" {self.arg1 * matsize}, {self.arg2 * matsize}, {self.arg3 * matsize}"
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

    # parse instrs, setup, and cleanup into Instruction objects
    # load the rest of the args into the Program object
    def __init__(self, instrs, setup, cleanup, distance, bitwidth, matsize, name, reset, absoluteaddrs, program_dir: str) -> 'Program':
        self.instrs = []
        self.setup = []
        self.cleanup = []

        for i in range(len(instrs)):
            self.instrs.append(Instruction(instrs[i]))

        if setup:
            for i in range(len(setup)):
                self.setup.append(Instruction(setup[i]))

        if cleanup:
            for i in range(len(cleanup)):
                self.cleanup.append(Instruction(cleanup[i]))

        self.distance = distance
        self.bitwidth = bitwidth
        self.matsize = matsize
        self.name = name
        self.reset = reset
        self.program_dir = program_dir
        self.absolute_addresses = absoluteaddrs

    def get_filepath(self, binary: bool, control: bool) -> str:
        filepath = self.program_dir
        if control:
            filepath += "/control"
        else:
            filepath += f"/{self.name}"
        if binary:
            return f"{filepath}.out"
        else:
            return f"{filepath}.a"
    
    # make a .a file for the program at the right location
    def generate_dot_a(self, control: bool) -> None:
        filepath = self.get_filepath(False, control)
        nop = Instruction("NOP")
        hlt = Instruction("HLT")

        with open(filepath, "w") as f:

            # all generated files should start with 50 NOPs (PCs 0-49)
            for _ in range(50):
                f.write(f"{nop.to_string(self.matsize, self.absolute_addresses)}\n")
            
            # after that, every 50th instruction is a setup instruction
            for i in range(len(self.setup)):
                f.write(f"{self.setup[i].to_string(self.matsize, self.absolute_addresses)}\n")
                for _ in range(49):
                    f.write(f"{nop.to_string(self.matsize, self.absolute_addresses)}\n")

            # then the instructions under test, self.distance instructions apart
            if len(self.instrs) != 2:
                raise ValueError("Please provide exactly two instructions to test.")
            f.write(f"{self.instrs[0].to_string(self.matsize, self.absolute_addresses)}\n")
            for _ in range(self.distance - 1):
                f.write(f"{nop.to_string(self.matsize, self.absolute_addresses)}\n")
            f.write(f"{self.instrs[1].to_string(self.matsize, self.absolute_addresses)}\n")

            # pad with NOPs so that the first cleanup instruction is 100 lines after the first instruction under test 
            for _ in range(99-self.distance):
                f.write(f"{nop.to_string(self.matsize, self.absolute_addresses)}\n")

            # after that, every 50th instruction is a cleanup instruction
            for i in range(len(self.cleanup)):
                f.write(f"{self.cleanup[i].to_string(self.matsize, self.absolute_addresses)}\n")
                for _ in range(49):
                    f.write(f"{nop.to_string(self.matsize, self.absolute_addresses)}\n")

            # finally, HLT
            f.write(f"{hlt.to_string(self.matsize, self.absolute_addresses)}\n")


# run the squish test given the args
def squish_test(instrs: list, distance: int, bitwidth: int, matsize: int, 
                name: str, setup: list, cleanup: list, reset: bool, 
                absoluteaddrs: bool, test_folder: str) \
    -> Tuple[bool, Dict[int, int]]:

    config.MATSIZE = matsize
    config.DWIDTH = bitwidth

    if len(instrs) != 2:
        print("Please provide two instructions to test.")
        exit(1)

    if distance < 1 or distance > 50:
        print("Distance must be between 1 and 50.")
        exit(1)

    # parse args into Program object
    program_dir = f"{os.path.dirname(__file__)}/{test_folder}/{name}"
    program = Program(instrs, setup, cleanup, distance, bitwidth, matsize, name, reset, absoluteaddrs, program_dir) 

    # make folder for the test (squish/name/) and add weights and inputs if they don't already exist
    weights_filename = make_weights(program_dir, program.matsize, program.bitwidth, 8)
    hostmem_filename = make_hostmem(program_dir, program.matsize, program.bitwidth, 8)


    # if -r is set, or the following don't exist, or the test name is default (test):
    # generate .a file for d=50 (control)
    if reset or not os.path.exists(program.get_filepath(binary=False, control=True)) or program.name == "test":
        program.generate_dot_a(control=True)

    # assemble into .out file for d=50 (control)
    if reset or not os.path.exists(program.get_filepath(binary=True, control=True)) or program.name == "test":
        assemble(f"{program_dir}/control.a", 0)

    # generate .a file (test)
    if reset or not os.path.exists(program.get_filepath(binary=False, control=False)) or program.name == "test":
        program.generate_dot_a(control=False)    

    # assemble into .out file (test)
    if reset or not os.path.exists(program.get_filepath(binary=True, control=False)) or program.name == "test":
        assemble(f"{program_dir}/{program.name}.a", 0)

    # run d=50 .out file (control) and get the resulting matrix and final trace
    print(f"Testing {name} for d = {distance}. b = {bitwidth}, m = {matsize}")
    print(f"Control")
    ctrl_output_filename = f"{program_dir}/ctrl_{config.DWIDTH}b_{config.MATSIZE}m"
    if reset or not os.path.exists(ctrl_output_filename + ".pkl") or program.name == "test":
        runtpu_ctrl_args = argparse.Namespace(prog=program.get_filepath(binary=True, control=True), hostmem=hostmem_filename, weightsmem=weights_filename)
        (ctrl_hostmem, ctrl_sim_trace) = runtpu(runtpu_ctrl_args, name=ctrl_output_filename)
    else:
        with open(ctrl_output_filename + ".pkl", "rb") as f:
            (ctrl_hostmem, ctrl_sim_trace) = pickle.load(f)

    # run runtpu.py in standard mode and get result
    print(f"Test")
    test_output_filename = f'{program_dir}/test_{config.DWIDTH}b_{config.MATSIZE}m_{distance}d'
    if reset or not os.path.exists(test_output_filename + ".pkl") or program.name == "test":
        runtpu_test_args = argparse.Namespace(prog=program.get_filepath(binary=True, control=False), hostmem=hostmem_filename, weightsmem=weights_filename)
        (test_hostmem, test_sim_trace) = runtpu(runtpu_test_args, name=test_output_filename)
    else:
        with open(test_output_filename + ".pkl", "rb") as f:
            (test_hostmem, test_sim_trace) = pickle.load(f)

    # compare results and output a verdict
    # comparison may include a diff (between control and test) of host memory as ndarray and trace at last cycle
    # let's just do a comparison of the host memory for now
    # print("Control host memory:")
    # print_mem(ctrl_hostmem)
    # print("Test host memory:")
    # print_mem(test_hostmem)

    if ctrl_hostmem == test_hostmem:
        print(f"Test {name} matches control")
        return True, test_hostmem
    else:
        print(f"Test failed! {name} does not match control")
        return False, test_hostmem


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

    squish_test(instrs, distance, bitwidth, matsize, name, 
                setup, cleanup, reset, absoluteaddrs)
