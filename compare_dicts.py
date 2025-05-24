# compare some old format union_{0.5/1}_{0.5/1}.json's with a new format
# results.json

import json

# load the jsons
with open(f"test/squish/may22_full_half_m4-m32/results.json", "r") as f:
    results = json.load(f)

unions = {}
for len1 in [0.5, 1]:
    unions[len1] = {}
    for len2 in [0.5, 1]:
        with open(f"union_{len1}_{len2}.json") as f:
            unions[len1][len2] = json.load(f)

# results has the format
# instr1(s)_instr2(s)
# b32
# m4
# l1=2_l2=2 | l1=2 | l2=2 (if applicable)
# hm2=hm1+/-n^?
# ub2=ub1+/-n^?
# acc2=acc1+/-n^?
# w0-w4 (values depend on what's there)

# unions has the format
# relative len 1 (0.5 or 1)
# relative len 2 (0.5 or 1)
# instr1_instr2_(diff/same_hm)?_(diff/same_ub)?_(diff/same_acc)?_(no/yes_s)?_(no/yes_s)?
# b32
# m4
# w0-w4 (values depend on what's there)

# if results doesn't have a length (or only one length), check it in all 
# relevant union lengths

# same maps to hm2=hm2+0
# diff maps to hm2=hm2-{matsize}^


def compare_result_to_union(result_val, union, result_path):

    # get all signals from result_val
    instr_combo = result_path[0]
    bitwidth = result_path[1]
    matsize = result_path[2]
    matsize_int = int(matsize[1:])

    ptr = 3
    signals = []
    for i, first_char in enumerate(["l", "h", "u", "a", "w"]):
        if len(result_path) > ptr and result_path[ptr][0] == first_char:
            signals.append(result_path[ptr])
            ptr += 1
        else:
            signals.append(None)
    
    lengths = signals[0]
    hm = signals[1]
    ub = signals[2]
    acc = signals[3]
    w = signals[4]

    # compute union test name: 
    # handle conversion from mmc/mmcs_... to mmc_..._no/yes_s
    # do same/diff_hm/ub/acc
    mmc_count = instr_combo.count("mmc") 
    mmcs_count = instr_combo.count("mmcs") 
    first_mmcs = instr_combo.find("mmcs")
    last_mmcs = instr_combo.rfind("mmcs")
    instr_combo = instr_combo.replace("mmcs", "mmc")

    union_name_components = [instr_combo]
    for (mem_val, mem_str) in zip([hm, ub, acc], ["hm", "ub", "acc"]):
        if mem_val is not None:
            if mem_val[-1] == "^": # no overlap
                union_name_components.append(f"diff_{mem_str}")
            else:
                union_name_components.append(f"same_{mem_str}")
    
    if mmcs_count > 0:
        if first_mmcs == 0:
            union_name_components.append("yes_s")
        else:
            union_name_components.append("no_s")
        if mmc_count == 2:
            if last_mmcs == 0:
                union_name_components.append("no_s")
            else:
                union_name_components.append("yes_s")
    else:
        for _ in range(mmc_count):
            union_name_components.append("no_s")

    # check what lengths to look in:
    has_l1 = lengths is not None and lengths.find("l1") != -1
    has_l2 = lengths is not None and lengths.find("l2") != -1
    relative_l1s = [0.5, 1]
    relative_l2s = [0.5, 1]
    if lengths is not None:
        lengths_list = lengths.split("_")
        if has_l1:
            relative_l1s = [int(lengths_list[0][lengths_list[0].find("=")+1:])/matsize_int]
        if has_l2:
            if has_l1:
                relative_l2s = [int(lengths_list[1][lengths_list[1].find("=")+1:])/matsize_int]
            else:
                relative_l2s = [int(lengths_list[0][lengths_list[0].find("=")+1:])/matsize_int]
    
    # do the check
    for rel_l1 in relative_l1s:
        for rel_l2 in relative_l2s:
            union_name = "_".join(union_name_components)
            union_val = union[rel_l1][rel_l2][union_name][bitwidth][matsize][w] 
            if union_val != result_val:
                print("result", end="")
                for item in result_path:
                    print(f"[{item}]", end="")
                print(f"= {result_val} vs. union[{rel_l1}][{rel_l2}][{union_name}][{bitwidth}][{matsize}][{w}] = {union_val}")             
                return False
    return True

def compare_union_to_result(union_val, result, union_path):
    l1 = union_path[0]
    l2 = union_path[1]
    union_name = union_path[2]
    bitwidth = union_path[3]
    matsize = union_path[4]
    matsize_int = int(matsize[1:])
    w = union_path[5]
    
    
    # generate results instr string
    instrs = "_".join(union_name.split("_")[0:2])
    mmc_count = union_name.count("mmc")
    no_s_count = union_name.count("no_s")
    yes_s_count = union_name.count("yes_s")
    # print("instrs", instrs, "mmc_count", mmc_count, "yes_s_count", yes_s_count)
    if mmc_count == yes_s_count:
        instrs = instrs.replace("mmc", "mmcs")
    if mmc_count == 2 and yes_s_count == 1:
        if union_name.find("yes_s_no_s") != -1: # it's the first MMC
            instrs = instrs[0:3] + "s" + instrs[3:]
        else:
            instrs += "s"
    # print("instrs after", instrs)
    # explore down the length branch
    result_str = f"result[{instrs}][{bitwidth}][{matsize}]"
    partial = result[instrs][bitwidth][matsize]
    next_key = next(iter(partial))
    if next_key[0] == "l": # we have a length
        has_l1 = next_key.find("l1") != -1
        has_l2 = next_key.find("l2") != -1
        result_length_components = []
        if has_l1:
            result_length_components.append(f"l1={int(matsize_int*l1)}")
        if has_l2: 
            result_length_components.append(f"l2={int(matsize_int*l2)}")
        full_length = "_".join(result_length_components)
        partial = partial[full_length]
        result_str += f"[{full_length}]"

    # explore down the hm, ub, and acc paths
    for mem in ["hm", "ub", "acc"]:
        next_key = next(iter(partial))
        if next_key[0] == mem[0]: 
            if union_name.find(f"same_{mem}") != -1:
                result_str += f"[{mem}2={mem}1+0]"
                partial = partial[f"{mem}2={mem}1+0"]
            elif union_name.find(f"diff_{mem}") != -1:
                result_str += f"[{mem}2={mem}1-{int(matsize_int*l2)}^]"
                partial = partial[f"{mem}2={mem}1-{int(matsize_int*l2)}^"]
            else:
                raise ValueError(f"union name missing {mem}, but result has it")

    if partial[w] != union_val:
        print(f"{result_str}[{w}] = {partial[w]} vs. union", end="")
        for item in union_path:
            print(f"[{item}]", end="")
        print(f" = {union_val}")
    return partial[w] == union_val

def compare_rec(test, control, test_path, comparison_func):
    total = 0
    total_correct = 0
    if type(test) is dict:
        for key in test.keys():
            test_path.append(key)
            t, tc = compare_rec(test[key], control, test_path, comparison_func)
            test_path.pop()
            total += t
            total_correct += tc
    else: # it's a value
        total += 1
        if comparison_func(test, control, test_path):
            total_correct += 1

    return total, total_correct

arr = []
print(compare_rec(results, unions, arr, compare_result_to_union))
print(compare_rec(unions, results, arr, compare_union_to_result))
