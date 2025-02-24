import sys
import os
import pickle

import numpy as np
from squishtest import ProgramType

# add base folder (OPENTGPTPU) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import runtpu

# test_name = "full_test_100d_small_matsizes"
test_name = "small_matsizes_50d_feb22"
test_type = "mmc_rw_full_yes_s"
program_type = ProgramType.Test
bitwidth = 32
matsize = 4
distance = 14
DEVICE_TYPE = "runtpu" # "runtpu" or "sim"

def get_file_name(file_name, test_name, test_type, program_type, bitwidth, matsize, distance):
    if program_type == ProgramType.Control:
        return f"test/squish/{test_name}/{test_type}/ctrl_{bitwidth}b_{matsize}m/{DEVICE_TYPE}_{file_name}.npy"
    elif program_type == ProgramType.Test:
        return f"test/squish/{test_name}/{test_type}/test_{bitwidth}b_{matsize}m_{distance}d/{DEVICE_TYPE}_{file_name}.npy"
    elif program_type == ProgramType.NoNop:
        return f"test/squish/{test_name}/{test_type}/nonop_{bitwidth}b_{matsize}m/{DEVICE_TYPE}_{file_name}.npy"


for memory in ["hostmem", "weightsmem", "ubuffer", "wqueue", "accmems"]:
    file_name = get_file_name(memory, test_name, test_type, program_type, bitwidth, matsize, distance)
    loaded_mem = np.load(file_name)
    print(f"{memory} for {file_name}:")
    print(loaded_mem)
