import sys
import os
import pickle
from squishtest import ProgramType

# add base folder (OPENTGPTPU) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import runtpu

# test_name = "full_test_100d_small_matsizes"
test_name = "full_test_nonop_attempt_2"
test_type = "mmc_rw_one_space_no_s"
program_type = ProgramType.NoNop
bitwidth = 32
matsize = 4
distance = 100

if program_type == ProgramType.Control:
    file_name = f"test/squish/{test_name}/{test_type}/ctrl_{bitwidth}b_{matsize}m/hostmem.pkl"
elif program_type == ProgramType.Test:
    file_name = f"test/squish/{test_name}/{test_type}/test_{bitwidth}b_{matsize}m_{distance}d/hostmem.pkl"
elif program_type == ProgramType.NoNop:
    file_name = f"test/squish/{test_name}/{test_type}/nonop_{bitwidth}b_{matsize}m/hostmem.pkl"
hostmem = pickle.load(open(file_name, "rb"))

print(f"Hostmem for {file_name}:")
runtpu.print_mem(hostmem, bits=bitwidth, size=matsize)
print(f"Hostmem for {file_name}:")