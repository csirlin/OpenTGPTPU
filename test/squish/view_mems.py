import sys
import os
import pickle

import numpy as np
from squishtest import ProgramType

# add base folder (OPENTGPTPU) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import runtpu

# test_name = "full_test_100d_small_matsizes"
test_name = "full_test_mar2_sim_control"
test_type = "rw_rw_same_weights_one_space"
program_type = ProgramType.Control
bitwidth = 32
matsize = 4
distance = 99

def get_file_name(file_name, test_name, test_type, program_type, bitwidth, matsize, distance):
    if program_type == ProgramType.Control:
        return f"test/squish/{test_name}/{test_type}/{program_type.value}_{bitwidth}b_{matsize}m/sim_{file_name}.npy"
    elif program_type == ProgramType.Distance:
        return f"test/squish/{test_name}/{test_type}/{program_type.value}_{bitwidth}b_{matsize}m_{distance}d/runtpu_{file_name}.npy"
    elif program_type == ProgramType.NoNop:
        return f"test/squish/{test_name}/{test_type}/{program_type.value}_{bitwidth}b_{matsize}m/runtpu_{file_name}.npy"


for memory in ["hostmem", "weightsmem", "ubuffer", "wqueue", "accmems"]:
    file_name = get_file_name(memory, test_name, test_type, program_type, bitwidth, matsize, distance)
    loaded_mem = np.load(file_name)
    print(f"{memory} for {file_name}:")
    print(loaded_mem)
