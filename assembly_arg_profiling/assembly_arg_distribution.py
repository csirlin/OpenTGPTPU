# find the distribution of assembly argument values. this is helpful for 
# learning how big the UB and ACC should be before address bits start getting
# truncated.

import glob

dist = {}
# assembly_files = ['test/mullifier_examples/test_simple_store/open_tpu.a', 
#                   'test/test_extend_hostmem/test_extend_hostmem.a', 
#                   'mullifier_rw_mmc_one_space_no_s/distance_16m_99d.a']
assembly_files = glob.glob("**/*.a", recursive=True)
for index, af in enumerate(assembly_files):
    if index % 1000 == 0:
        print(f"Processing {index} of {len(assembly_files)} assembly files")
    with open(af, "r") as f:
        try:
            s = f.read()
        except UnicodeDecodeError:
            print(f"Error reading file {af}, skipping")
            continue
        for word in s.split():
            word = word.replace(",", "")
            if word.isnumeric():
                if int(word) in dist:
                    dist[int(word)] += 1
                else:
                    dist[int(word)] = 1
    
# sort the dictionary by key
dist = dict(sorted(dist.items()))
print(dist)