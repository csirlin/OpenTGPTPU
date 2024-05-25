import pickle
from sys import stdout
import pyrtl

with open('branch_eq_pyrtl/pickled.pkl', 'rb') as file:
	sim_trace = pickle.load(file)

wires = []
for wn in sim_trace.trace:
	if wn.find('const') != 0:
		wires.append(wn)
wires.sort()

objs = []
for wn in wires:
	objs.append(sim_trace.trace[wn])

print(len(objs), len(objs[0]))

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
	vals1 = sim_trace.trace[wire_name]
	for i in range(len(vals1)):
		print(f"#{i}: {wire_name} = {vals1[i]}", file=file)
	if file != stdout:
		file.close()
# for wn in sim_trace2.trace:
# 	print(len(sim_trace2.wires_to_track))