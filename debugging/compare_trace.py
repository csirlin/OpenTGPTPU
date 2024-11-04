import pickle
from sys import stdout
import pyrtl


# load pyrtl traces from pickle file
with open('../test/test_rhm/pickled_32_8x8_0_0_24.pkl', 'rb') as file:
	sim_trace1 = pickle.load(file)

with open('../test/test_rhm/pickled_32_8x8_4_4_20.pkl', 'rb') as file:
	sim_trace2 = pickle.load(file)

# get all the non-const wire names
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

# load all the shared wires into objs1 and objs2
# objs1[i][j] is the value of wire i (in alphabetical order excluding wires not in sim_trace2) at cycle j
# and vice-versa for objs2[i][j]
wire_names = sorted(list(t1_wires.intersection(t2_wires)))

t1_objs = []
for wn in wire_names:
	t1_objs.append(sim_trace1.trace[wn])

t2_objs = []
for wn in wire_names:
	t2_objs.append(sim_trace2.trace[wn])


# print all the differences between each wire in trace1 and trace2 for every cycle
def print_all_diffs():
	with open('differences.txt', 'w') as file:
		diffs = False

		# for each cycle...
		for i in range(min(len(t1_objs[0]), len(t2_objs[0]))):
			inequality = False
			
			# ...print each wire with a different value in the two traces
			for j in range(len(t1_objs)):
				if t1_objs[j][i] != t2_objs[j][i] and not (t1_objs[j][i] == 8 and t2_objs[j][i] == 32):
					if not inequality: # only print cycle number if there are differences in that cycle, and only once
						inequality = True
						print(f"Timestep #{i}:", file=file)
					print(f"\t{wire_names[j]}: {t1_objs[j][i]} vs {t2_objs[j][i]}", file=file)
					diffs = True
		
		# print if there are no differences to rule out any bugs that would incorrectly leave the file empty
		if not diffs: 
			print("No differences found.", file=file)


# compare a single wire between traces for every cycle
def print_wire_2(wire_name, file=stdout):
	if file != stdout:
		file = open(file, 'w')
	
	vals1 = t1_objs[wire_names.index(wire_name)]
	vals2 = t2_objs[wire_names.index(wire_name)]

	# for every value in the wire in each trace, print their values and if they're the same or not
	for i in range(min(len(vals1), len(vals2))):
		if vals1[i] == vals2[i]:
			print(f"#{i}: {wire_name} (same) = {vals1[i]}", file=file)
		else:
			print(f"#{i}: {wire_name} (diff) = {vals1[i]} vs {vals2[i]}", file=file)
	
	if file != stdout:
		file.close()


# print a single wire for every cycle
# "num" should be 1 or 2 to select the trace
def print_wire_1(trace_num, wire_name, file=stdout):
	if file != stdout:
		file = open(file, 'w')

	vals = []
	if trace_num == 1:
		vals = t1_objs[wire_names.index(wire_name)]
	if trace_num == 2:
		vals = t2_objs[wire_names.index(wire_name)]

	for i in range(len(vals)):
		print(f"#{i}: {wire_name} = {vals[i]}", file=file)

	if file != stdout:
		file.close()


# print every wire for a given trace and cycle
def full_cycle_1(trace_num, cycle_num, file=stdout):
	if file != stdout:
		file = open(file, 'w')

	if trace_num == 1:
		for i in range(len(t1_objs)):
			print(f"{wire_names[i]} = {t1_objs[i][cycle_num]}", file=file)
	if trace_num == 2:
		for i in range(len(t2_objs)):
			print(f"{wire_names[i]} = {t2_objs[i][cycle_num]}", file=file)

	if file != stdout:
		file.close()
