import glob
import subprocess
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from runtpu import runtpu
from sim import TPUSim
from utils import load_and_compare_all_mems

# run all examples in test/mullifier_examples
# run from OpenTGPTPU as current directory

base_path = "test/mullifier_examples"

# first character of folder must be a lowercase letter. this excludes tests that 
# start with an underscore, which have compiler errors and should be ignored
test_folders = sorted(glob.glob(f"{base_path}/[a-z]*/"))
for tf in test_folders:
    # if tf.find("/bfsbig/") == -1:
    #     continue
    print(tf)
    test_path = f"{base_path}/{tf.split('/')[-2]}"

    # run hardware and software sims
    runtpu(f"{test_path}/open_tpu.out", f"{test_path}/input.npy", 
           f"{test_path}/weights.npy", bitwidth=32, matsize=8, 
           output_folder=f"{test_path}/runtpu", output_trace=True)
    
    sim = TPUSim(f"{test_path}/open_tpu.out", f"{test_path}/input.npy", 
                 f"{test_path}/weights.npy", bitwidth=32, matsize=8, 
                 output_folder=f"{test_path}/sim")
    sim.run()

    # compare results between the two
    load_and_compare_all_mems(test_path)

