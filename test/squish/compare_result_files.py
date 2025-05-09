# compare two json result files generated by squishtests
import sys
import glob
import json
squish_folder_1 = sys.argv[1]
squish_folder_2 = sys.argv[2]

# get all the json filenames
json_paths_1 = glob.glob(f"{squish_folder_1}/*.json")
json_paths_2 = glob.glob(f"{squish_folder_2}/*.json")
json_names_1 = [p.split("/")[-1] for p in json_paths_1]
json_names_2 = [p.split("/")[-1] for p in json_paths_2]
json_names_1.sort()
json_names_2.sort()

# load each json file and compare, print both if they differ  
for name in set(json_names_1).intersection(set(json_names_2)):
    print(f"Comparing {name}")
    with open(f"{squish_folder_1}/{name}", "r") as f:
        json_1 = json.load(f)
    with open(f"{squish_folder_2}/{name}", "r") as f:
        json_2 = json.load(f)
    if json_1 != json_2:
        print(f"Files {name} differ")
        print(json_1)
        print(json_2)
