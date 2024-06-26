import pickle
from sys import stdout
import pyrtl

# with open('32_8x8_no_preload/pickled_32_8x8.pkl', 'rb') as file:
with open('andrews_example/runtpu/pickled_32_8x8.pkl', 'rb') as file:
	sim_trace = pickle.load(file)

wires = set()
for wn in sim_trace.trace:
	if wn.find('const') != 0:
		wires.add(wn)

wire_names = sorted(list(wires))
objs = []
for wn in wire_names:
	objs.append(sim_trace.trace[wn])

# for i in range(len(t1_objs)):
# 	if len(t1_objs[i]) != 601:
# 		print(f"len(t1_objs[{i}]) == {len(t1_objs[i])}")
# 		print(f"t1_wires[{i}] == {t1_wires[i]}")

# def print_all_diffs():
# 	with open('differences.txt', 'w') as file:
# 		for i in range(len(t1_objs[0])):
# 			inequality = False
# 			for j in range(len(t1_objs)):
# 				if t1_objs[j][i] != t2_objs[j][i]:
# 					if not inequality:
# 						inequality = True
# 						print(f"Timestep #{i}:", file=file)
# 					print(f"\t{t1_wires[j]}: {t1_objs[j][i]} vs {t2_objs[j][i]}", file=file)

# def print_wire_2(wire_name, file=stdout):
# 	if file != stdout:
# 		file = open(file, 'w')
# 	vals1 = sim_trace1.trace[wire_name]
# 	vals2 = sim_trace2.trace[wire_name]
# 	for i in range(len(vals1)):
# 		if vals1[i] == vals2[i]:
# 			print(f"#{i}: {wire_name} (same) = {vals1[i]}", file=file)
# 		else:
# 			print(f"#{i}: {wire_name} (diff) = {vals1[i]} vs {vals2[i]}", file=file)
# 	if file != stdout:
# 		file.close()

def print_wire_1(wire_name, file=stdout):
	if file != stdout:
		file = open(file, 'w')
	vals = objs[wire_names.index(wire_name)]
	for i in range(len(vals)):
		print(f"#{i}: {wire_name} = {vals[i]}", file=file)
	if file != stdout:
		file.close()

def print_wire_cat(wire_prefix, file=stdout):
	cycles = len(objs[0])
	if file != stdout:
		file = open(file, 'w')
	vals = []
	wire_name_list = []
	for wn in wire_names:
		if wn.find(wire_prefix) == 0:
			wire_name_list.append(wn)
			vals.append(objs[wire_names.index(wn)])
	for i in range(len(vals[0])):
		print(f"#{i}:", file=file)
		for j in range(len(wire_name_list)):
			print(f"\t{wire_name_list[j]} = {vals[j][i]}", file=file)
	if file != stdout:
		file.close()

def print_cycle_diff(file=stdout):
	if file != stdout:
		file = open(file, 'w')
	for i in range(1, len(objs[0])):
		print(f"Cycle {i-1} -> {i}:", file=file)
		print(i, end = ' ')
		for wn in wire_names:
			if objs[wire_names.index(wn)][i] != objs[wire_names.index(wn)][i-1]:
				print(f"\t{wn}: {objs[wire_names.index(wn)][i-1]} -> {objs[wire_names.index(wn)][i]}", file=file)
	if file != stdout:
		file.close()
# for wn in sim_trace2.trace:
# 	print(len(sim_trace2.wires_to_track))