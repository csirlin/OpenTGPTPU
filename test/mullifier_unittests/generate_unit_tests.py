import glob
import sys
import os
import numpy as np
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../squish/"))
)
from squishtest import Instruction, Operation
from assembler import assemble
from generate import make_hostmem, make_weights
from runtpu import runtpu
from sim import TPUSim
from utils import run_and_compare_all_mems


# hostmem length in units of matsizes. so if HM_ADDR_SIZE is 8 and matsize is 
# 16, hostmem length is 128 addresses
HM_ADDR_BLOCKS = 16 
UB_ADDR_BLOCKS = 16
WM_ADDR_BLOCKS = 16
BITWIDTH = 32
MATSIZE = 8

UNSIGNED_DTYPES = {
    8: np.uint8,
    16: np.uint16,
    32: np.uint32,
    64: np.uint64
}

def twos_comp(val, bits):
    return val if val >= 0 else (1 << bits) + val

### GENERATE ASSEMBLY INSTRUCTIONS ###

# for tests 1, 3, 10
def prog_act_branch_forward(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("RW 0")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"MMC.S 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"ACT 0, {matsize}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs += [f"RHM {2*matsize}, {2*matsize}, 1", "NOP"] * 50
    instrs.append("HLT")
    instrs += [f"RHM {3*matsize}, {3*matsize}, 1", "NOP"] * 50
    return instrs

# for tests 2, 4, 11
def prog_act_branch_backward(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("RW 0")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"MMC.S 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"ACT 0, {matsize}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs += [f"RHM {3*matsize}, {3*matsize}, 1", "NOP"] * 50
    instrs.append("HLT")
    instrs += [f"RHM {4*matsize}, {4*matsize}, 1", "NOP"] * 50
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("RW 1")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"MMC.S {matsize}, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"ACT {matsize}, {2*matsize}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs += [f"RHM {5*matsize}, {5*matsize}, 1", "NOP"] * 50
    return instrs

# for tests 5, 6, 7, 8, 9, 12
def prog_act_no_branch(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("RW 0")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"MMC.S 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"ACT 0, {matsize}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"RHM {2*matsize}, {2*matsize}, 1")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

# for test 13
def prog_rhm_cell(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, {matsize*(UB_ADDR_BLOCKS-1)}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("RHM.S 0, 0, 0")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

# for test 14
def prog_rhm_vec(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, {matsize*(UB_ADDR_BLOCKS-1)}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"RHM.S 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

# for test 15
def prog_rhm_pc_ret(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM.C {2*matsize}, {matsize}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

# for test 16
def prog_rhm_normal(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

# for test 17
def prog_whm_cell(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, {matsize*(UB_ADDR_BLOCKS-1)}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"WHM.S 0, {matsize*(UB_ADDR_BLOCKS-1)}, 0")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

# for test 18
def prog_whm_vec(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, {matsize*(UB_ADDR_BLOCKS-1)}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"WHM.S 0, {matsize*(UB_ADDR_BLOCKS-1)}, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

# for test 19
def prog_whm_normal(matsize, is_nop):
    instrs = []
    if is_nop: instrs += ["NOP"] * 50
    instrs.append(f"RHM 0, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append(f"WHM {matsize}, 0, {matsize}")
    if is_nop: instrs += ["NOP"] * 49
    instrs.append("HLT")
    return instrs

### GENERATE HOSTMEM ###

# default hostmem [[1 ... M], [M+1 ... 2M], ...]
def hm_default(matsize):
    return np.arange(1, HM_ADDR_BLOCKS * matsize**2 + 1) \
             .reshape(HM_ADDR_BLOCKS * matsize, matsize) \
             .astype(UNSIGNED_DTYPES[BITWIDTH])

# replace the first M rows of hostmem with identity matrix
def hm_one_identity(matsize):
    hm = hm_default(matsize)
    for i in range(matsize):
        for j in range(matsize):
            if i == j:
                hm[i][j] = 1
            else:
                hm[i][j] = 0
    return hm

### GENERATE WEIGHTSMEM ###

# default weights [[[1 ... M^2]], [[M^2+1 ... 2M^2]], ...]
def wm_default(matsize):
    wm = np.zeros((WM_ADDR_BLOCKS, matsize, matsize), 
                  dtype=UNSIGNED_DTYPES[BITWIDTH])
    for i in range(WM_ADDR_BLOCKS):
        wm[i] = np.arange(i * matsize**2 + 1, (i+1)*matsize**2 + 1) \
                  .reshape(matsize, matsize)
    return wm

# set up weight(s) for branch instructions (assumes it's multiplied with 
# identity matrix in UB)
# branches have the first row [taken, not taken, X, ..., X,  1, 1]
#                          or [not taken, taken, X, ..., X, ~1, 1]
#                                branch_size^      branch_val^
# optionally supports a second branch_size and branch_val to create a second
# branch weight
def wm_branch(matsize, branch_size_1, branch_val_1, 
                       branch_size_2=None, branch_val_2=None):
    wm = wm_default(matsize)
    other_branch_1 = (branch_size_1 + 10000)%(2**32)

    if branch_val_1 == 1:
        wm[0][0][0] = branch_size_1
        wm[0][0][1] = other_branch_1
    else:
        wm[0][0][0] = other_branch_1
        wm[0][0][1] = branch_size_1
    wm[0][0][-1] = 1
    wm[0][0][-2] = branch_val_1

    if branch_size_2 is None or branch_val_2 is None:
        return wm
    
    other_branch_2 = (branch_size_2 + 10000)%(2**32)
    if branch_val_2 == 1:
        wm[1][0][0] = branch_size_2
        wm[1][0][1] = other_branch_2
    else:
        wm[1][0][0] = other_branch_2
        wm[1][0][1] = branch_size_2
    wm[1][0][-1] = 1
    wm[1][0][-2] = branch_val_2

    return wm

# set up weight for equality check instructions (assumes it's multiplied with 
# identity matrix in UB)
# equality instrs have the first row [ 0, X, ..., X, 2] for a true check
#                                 or [~0, X, ..., X, 2] for a false check
#                                   val^
def wm_equality(matsize, val):
    wm = wm_default(matsize)
    wm[0][0][0] = val
    wm[0][0][-1] = 2
    return wm

# set up weight for less than check instructions (assumes it's multiplied with
# identity matrix in UB)
# less than instrs have the first row [val, X, ..., X, 3], where it's true if
# val < 0 and false otherwise
def wm_less_than(matsize, val):
    wm = wm_default(matsize)
    wm[0][0][0] = val
    wm[0][0][-1] = 3
    return wm

# set up weight for jump instructions (assumes it's multiplied with identity 
# matrix in UB)
# jump instrs have the first row [destination_pc, X, ..., X, 4]
# optionally supports a second pc to create a second jump weight
def wm_jump(matsize, pc_1, pc_2=None):
    wm = wm_default(matsize)
    wm[0][0][1] = pc_1
    wm[0][0][-1] = 4

    if pc_2 is None:
        return wm
    
    wm[1][0][1] = pc_2
    wm[1][0][-1] = 4
    return wm

# set up weight for normal activation instructions. ensures top right corner is
# not 1, 2, 3, or 4
def wm_normal(matsize):
    wm = wm_default(matsize)
    wm[0][0][-1] = 42
    return wm

### GENERATE FILES ###

# generate assembly instructions for all mullifier unit tests
def generate_assembly(matsize):
    # get all regular (no-nop) assembly instructions
    reg_act_branch_forward = prog_act_branch_forward(matsize, False)
    reg_act_branch_backward = prog_act_branch_backward(matsize, False)
    reg_act_no_branch = prog_act_no_branch(matsize, False)
    reg_instruction_map = [
        reg_act_branch_forward,
        reg_act_branch_backward,
        reg_act_branch_forward,
        reg_act_branch_backward,
        reg_act_no_branch,
        reg_act_no_branch,
        reg_act_no_branch,
        reg_act_no_branch,
        reg_act_no_branch,
        reg_act_branch_forward,
        reg_act_branch_backward,
        reg_act_no_branch,
        prog_rhm_cell(matsize, False),
        prog_rhm_vec(matsize, False),
        prog_rhm_pc_ret(matsize, False),
        prog_rhm_normal(matsize, False),
        prog_whm_cell(matsize, False),
        prog_whm_vec(matsize, False),
        prog_whm_normal(matsize, False)
    ]

    # get all nop assembly instructions
    nop_act_branch_forward = prog_act_branch_forward(matsize, True)
    nop_act_branch_backward = prog_act_branch_backward(matsize, True)
    nop_act_no_branch = prog_act_no_branch(matsize, True)
    nop_instruction_map = [
        nop_act_branch_forward,
        nop_act_branch_backward,
        nop_act_branch_forward,
        nop_act_branch_backward,
        nop_act_no_branch,
        nop_act_no_branch,
        nop_act_no_branch,
        nop_act_no_branch,
        nop_act_no_branch,
        nop_act_branch_forward,
        nop_act_branch_backward,
        nop_act_no_branch,
        prog_rhm_cell(matsize, True),
        prog_rhm_vec(matsize, True),
        prog_rhm_pc_ret(matsize, True),
        prog_rhm_normal(matsize, True),
        prog_whm_cell(matsize, True),
        prog_whm_vec(matsize, True),
        prog_whm_normal(matsize, True)
    ]

    # iterate through each mullifier_unittest folder and create both types of 
    # assembly file
    folder_paths = [f for f in glob.glob(os.path.dirname(__file__) + "/[0-9]*")]
    for folder_path in folder_paths:
        folder_name = folder_path[folder_path.rfind(os.sep)+1:]
        folder_num = int(folder_name[:folder_name.find("_")])

        # write each instruction on a new line for reg and nop versions
        with open(folder_path + os.sep + f"reg_{matsize}m.a", "w") as f:
            for instr in reg_instruction_map[folder_num-1]:
                f.write(instr + "\n")
        
        with open(folder_path + os.sep + f"nop_{matsize}m.a", "w") as f:
            for instr in nop_instruction_map[folder_num-1]:
                f.write(instr + "\n")

# generate machine code from all assembly files
def generate_machine_code(matsize):
    folder_paths = [f for f in glob.glob(os.path.dirname(__file__) + "/[0-9]*")]
    for folder_path in folder_paths:
        assemble(folder_path + os.sep + f"reg_{matsize}m.a", 0)
        assemble(folder_path + os.sep + f"nop_{matsize}m.a", 0)

# generate hostmems for all tests
def generate_hostmem(matsize, bitwidth):
    hostmem_default = hm_default(matsize)
    hostmem_identity = hm_one_identity(matsize)

    # iterate through each mullifier_unittest folder and create hostmem files 
    # for each test. hostmem is identical regardless of nop/reg. tests 1-12 need
    # identity matrix, tests 13-19 can use default hostmem
    folder_paths = [f for f in glob.glob(os.path.dirname(__file__) + "/[0-9]*")]
    for folder_path in folder_paths:
        folder_name = folder_path[folder_path.rfind(os.sep)+1:]
        folder_num = int(folder_name[:folder_name.find("_")])

        if folder_num < 13:
            np.save(folder_path + os.sep + f"hostmem_{bitwidth}b_{matsize}m", 
                    hostmem_identity.astype(UNSIGNED_DTYPES[bitwidth]))
        else:
            np.save(folder_path + os.sep + f"hostmem_{bitwidth}b_{matsize}m", 
                    hostmem_default.astype(UNSIGNED_DTYPES[bitwidth]))

# generate weightsmems for all tests
def generate_weightsmem(matsize, bitwidth):
    # get weight matrices for each reg test
    reg_weight_map = [
        wm_branch(matsize, 100, 1),
        wm_branch(matsize, 201, 1, twos_comp(-104, bitwidth), 1),
        wm_branch(matsize, 100, 0),
        wm_branch(matsize, 201, 0, twos_comp(-104, bitwidth), 0),
        wm_equality(matsize, 0),
        wm_equality(matsize, 42),
        wm_less_than(matsize, twos_comp(-15, bitwidth)),
        wm_less_than(matsize, 0),
        wm_less_than(matsize, 15),
        wm_jump(matsize, 104),
        wm_jump(matsize, 205, 104),
        wm_normal(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize)
    ]

    # get weight matrices for each nop test
    nop_weight_map = [
        wm_branch(matsize, 148, 1),
        wm_branch(matsize, 298, 1, twos_comp(-252, bitwidth), 1),
        wm_branch(matsize, 148, 0),
        wm_branch(matsize, 298, 0, twos_comp(-252, bitwidth), 0),
        wm_equality(matsize, 0),
        wm_equality(matsize, 42),
        wm_less_than(matsize, twos_comp(-15, bitwidth)),
        wm_less_than(matsize, 0),
        wm_less_than(matsize, 15),
        wm_jump(matsize, 350),
        wm_jump(matsize, 500, 350),
        wm_normal(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize),
        wm_default(matsize)
    ]

    # iterate through each mullifier_unittest folder and create weightsmem files 
    folder_paths = [f for f in glob.glob(os.path.dirname(__file__) + "/[0-9]*")]
    for folder_path in folder_paths:
        folder_name = folder_path[folder_path.rfind(os.sep)+1:]
        folder_num = int(folder_name[:folder_name.find("_")])

        np.save(folder_path + os.sep + f"reg_weights_{bitwidth}b_{matsize}m", 
                reg_weight_map[folder_num-1].astype(UNSIGNED_DTYPES[bitwidth]))
        np.save(folder_path + os.sep + f"nop_weights_{bitwidth}b_{matsize}m", 
                nop_weight_map[folder_num-1].astype(UNSIGNED_DTYPES[bitwidth]))
        
### FUNCTION TO RUN TESTS ###

# invoke sim and runtpu to run the generated tests with the generated files
# pick either reg or nop
def run_tests(matsize, bitwidth, program_type):
    # iterate through each mullifier_unittest folder and run the test 
    folder_paths = [f for f in glob.glob(os.path.dirname(__file__) + "/[0-9]*")]
    for folder_path in folder_paths:
        folder_name = folder_path[folder_path.rfind(os.sep)+1:]
        print("Testing " + folder_name)
        
        prog_name = folder_path + os.sep + f"{program_type}_{matsize}m.out"
        hm_name = folder_path + os.sep + f"hostmem_{bitwidth}b_{matsize}m.npy"
        wm_name = folder_path + os.sep + \
                  f"{program_type}_weights_{bitwidth}b_{matsize}m.npy"
        output_base = folder_path + os.sep + f"{program_type}_"

        run_and_compare_all_mems(prog_name, hm_name, wm_name, folder_name, 
                         output_base, bitwidth, matsize)

### RUN TESTS ###

if __name__ == "__main__":  
    generate_assembly(MATSIZE)
    generate_machine_code(MATSIZE)
    generate_hostmem(MATSIZE, BITWIDTH)
    generate_weightsmem(MATSIZE, BITWIDTH)

    # run_tests(MATSIZE, BITWIDTH, "reg")
    run_tests(MATSIZE, BITWIDTH, "nop")
