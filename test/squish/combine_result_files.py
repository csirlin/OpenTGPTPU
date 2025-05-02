# combine all the squishtest result jsons into a unified file for easier
# exploration
import sys
import glob
import json
squish_folder = sys.argv[1]

# get all the json filenames
json_paths = glob.glob(f"{squish_folder}/*.json")
json_names = [p.split("/")[-1] for p in json_paths]
json_names.sort()

# combine into union dict
union_dict = {}
for name_1 in ["rhm", "whm", "rw", "mmc", "act"]:
    for name_2 in ["rhm", "whm", "rw", "mmc", "act", "hlt"]:
        if f"{name_1}_{name_2}.json" in json_names:
            with open(f"{squish_folder}/{name_1}_{name_2}.json", "r") as f:
                json_data = json.load(f)
            union_dict.update(json_data)

with open(f"{squish_folder}/union.json", "w") as f:
    json.dump(union_dict, f, indent=2)
