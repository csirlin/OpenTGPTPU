# Compare hostmems between all trials in two tests.
# valid test types are "ctrl", "test", and "nonop"
import os
import glob
import pickle
from squishtest import ProgramType

TEST_FOLDER_1 = "full_test_100d_small_matsizes"
TEST_FOLDER_2 = "full_test_nonop_attempt_2"
TYPE_1 = ProgramType.Control.value #ProgramType.Control
TYPE_2 = ProgramType.NoNop.value #ProgramType.NoNop

# Find the subset of tests that are common to both folders
tests_1 = set([os.path.basename(x) for x in glob.glob(f"{TEST_FOLDER_1}/*") if os.path.isdir(x)])
tests_2 = set([os.path.basename(x) for x in glob.glob(f"{TEST_FOLDER_2}/*") if os.path.isdir(x)])
tests_common = tests_1.intersection(tests_2)
print(f"Common tests: {tests_common}, {len(tests_common)}")

# full_test_100d_all_matsizes/act_act_diff_ub_diff_acc/ctrl_16b_4m/hostmem.pkl
# full_test_nonop_attempt_2/act_act_diff_ub_diff_acc/nonop_32b_32m/hostmem.pkl
# look at the hostmems that are common to both executions of each test
for test in tests_common:
    print(f"Comparing hostmems for {test}")

    # get all the folder names that hold hostmems. They look like ctrl_32b_8m or nonop_32b_8m
    subfolders_1 = glob.glob(f"{TEST_FOLDER_1}/{test}/{TYPE_1}*")
    subfolders_2 = glob.glob(f"{TEST_FOLDER_2}/{test}/{TYPE_2}*")
    subfolders_1 = set([os.path.basename(x) for x in subfolders_1])
    subfolders_2 = set([os.path.basename(x) for x in subfolders_2])
    # get the subset of trials that are common to both folders (in the format 32b_8m)
    trials_1 = set([x[x.find("_")+1:] for x in subfolders_1])
    trials_2 = set([x[x.find("_")+1:] for x in subfolders_2])
    trials_common = trials_1.intersection(trials_2)

    # compare hostmems for each trial, report any mismatches
    for trial in trials_common:
        hostmem_path_1 = f"{TEST_FOLDER_1}/{test}/{TYPE_1}_{trial}/hostmem.pkl"
        hostmem_path_2 = f"{TEST_FOLDER_2}/{test}/{TYPE_2}_{trial}/hostmem.pkl"

        hostmem_1 = pickle.load(open(hostmem_path_1, "rb"))
        hostmem_2 = pickle.load(open(hostmem_path_2, "rb"))

        if hostmem_1 == hostmem_2:
            print(f"{test}/{trial} hostmems match")
        else:
            print(f"{test}/{trial} hostmems are different")
            print(f"Hostmem {hostmem_path_1}: {hostmem_1}")
            print(f"Hostmem {hostmem_path_2}: {hostmem_2}")
            print("\n")

