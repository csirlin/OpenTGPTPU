# multithreaded caller to run all squishtests in parallel
# calls entry_point_full_test.py on separate threads to run the full test suite
# for different combinations of instr1, instr2, L1, and L2

import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# create a list of commands to run
commands = []
test_folder_base = "may8_d110"
categories = ['rhm', 'whm', 'rw', 'mmc', 'act', 'hlt']
for c1 in categories[:-1]:
    for c2 in categories:
        for l1 in [0.5, 1]:
            for l2 in [0.5, 1]:
                commands.append(["python", "entry_point_full_test.py", c1 + '_' + c2, str(l1), str(l2), test_folder_base + f"_{l1}_{l2}"])

# issue max_workers threads in parallel, automatically launching a new thread
# when one finishes
def run_command(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

ts = time.time()
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(run_command, cmd) for cmd in commands]

    for future in as_completed(futures):
        result = future.result()
        print(result.stdout)
        print(result.stderr)
tf = time.time()

print(f"All tests completed in {tf - ts:.2f} seconds.")
