import sys
import os
import pickle

# add base folder (OPENTGPTPU) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import runtpu

test_name = "full_test_100d_all_matsizes"
test_type = "rw_mmc_empty_no_s"
control = False
bitwidth = 32
matsize = 4
distance = 3

if control:
    file_name = f"test/squish/{test_name}/{test_type}/ctrl_{bitwidth}b_{matsize}m/hostmem.pkl"
else:
    file_name = f"test/squish/{test_name}/{test_type}/test_{bitwidth}b_{matsize}m_{distance}d/hostmem.pkl"
hostmem = pickle.load(open(file_name, "rb"))

print(f"Hostmem for {file_name}:")
runtpu.print_mem(hostmem, bits=bitwidth, size=matsize)
print(f"Hostmem for {file_name}:")