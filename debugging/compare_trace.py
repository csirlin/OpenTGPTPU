import pickle
from sys import stdout
import pyrtl


# load traces
with open('../test/andrews_example/nop/pickled_32_8x8.pkl', 'rb') as file:
	sim_trace1 = pickle.load(file)

# with open('branch_eq_pyrtl_32_16x16/pickled_32_16x16_before_matsize_changes.pkl', 'rb') as file:
with open('../test/andrews_example/nop/pickled_32_8x8_mod.pkl', 'rb') as file:
	sim_trace2 = pickle.load(file)


# sets of wire names
t1_wires = set()
for wn in sim_trace1.trace:
	if wn.find('const') != 0:
		t1_wires.add(wn)

t2_wires = set()
for wn in sim_trace2.trace:
	if wn.find('const') != 0:
		t2_wires.add(wn)

# union = t1_wires.union(t2_wires)
# diff1 = t1_wires.difference(t2_wires)
# diff2 = t2_wires.difference(t1_wires)
# diff = diff1.union(diff2)
# print(diff)

wire_names = sorted(list(t1_wires.intersection(t2_wires)))
# print(wire_names)

# get wire traces for each wire name indexed together
t1_objs = []
for wn in wire_names:
	t1_objs.append(sim_trace1.trace[wn])

t2_objs = []
for wn in wire_names:
	t2_objs.append(sim_trace2.trace[wn])


print(len(t1_objs), len(t2_objs), len(t1_objs[0]), len(t2_objs[0]))

# for i in range(len(t1_objs)):
# 	if len(t1_objs[i]) != 601:
# 		print(f"len(t1_objs[{i}]) == {len(t1_objs[i])}")
# 		print(f"t1_wires[{i}] == {t1_wires[i]}")

def print_all_diffs():
	with open('differences.txt', 'w') as file:
		diffs = False
		for i in range(min(len(t1_objs[0]), len(t2_objs[0]))):
			inequality = False
			for j in range(min(len(t1_objs), len(t1_objs))):
				if t1_objs[j][i] != t2_objs[j][i] and not (t1_objs[j][i] == 8 and t2_objs[j][i] == 32):
					if not inequality:
						inequality = True
						print(f"Timestep #{i}:", file=file)
					print(f"\t{wire_names[j]}: {t1_objs[j][i]} vs {t2_objs[j][i]}", file=file)
					diffs = True
		if not diffs:
			print("No differences found.", file=file)

def print_wire_2(wire_name, file=stdout):
	if file != stdout:
		file = open(file, 'w')
	vals1 = t1_objs[wire_names.index(wire_name)]
	vals2 = t2_objs[wire_names.index(wire_name)]
	for i in range(min(len(vals1), len(vals2))):
		if vals1[i] == vals2[i]:
			print(f"#{i}: {wire_name} (same) = {vals1[i]}", file=file)
		else:
			print(f"#{i}: {wire_name} (diff) = {vals1[i]} vs {vals2[i]}", file=file)
	if file != stdout:
		file.close()

def print_wire_1(num, wire_name, file=stdout):
	if file != stdout:
		file = open(file, 'w')
	vals = []
	if num == 1:
		vals = t1_objs[wire_names.index(wire_name)]
	if num == 2:
		vals = t2_objs[wire_names.index(wire_name)]
	for i in range(len(vals)):
		print(f"#{i}: {wire_name} = {vals[i]}", file=file)
	if file != stdout:
		file.close()

def full_cycle_1(num, cycle, file=stdout):
	if file != stdout:
		file = open(file, 'w')
	if num == 1:
		for i in range(len(t1_objs)):
			print(f"{wire_names[i]} = {t1_objs[i][cycle]}", file=file)
	if num == 2:
		for i in range(len(t2_objs)):
			print(f"{wire_names[i]} = {t2_objs[i][cycle]}", file=file)
# for wn in sim_trace2.trace:
# 	print(len(sim_trace2.wires_to_track))