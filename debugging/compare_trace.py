import pickle
from sys import stdout, set_int_max_str_digits
import pyrtl

set_int_max_str_digits(10000)

# load pyrtl traces from pickle file
with open('../mmc_rw_empty_no_s_32b_32m_74d/trace.pkl', 'rb') as file:
	sim_trace1 = pickle.load(file)

with open('../mmc_rw_empty_no_s_32b_32m_75d/trace.pkl', 'rb') as file:
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

		trace1_cycle_len = len(t1_objs[0])
		trace2_cycle_len = len(t2_objs[0])
		common_cycle_len = min(trace1_cycle_len, trace2_cycle_len)
		wire_count = len(t1_objs)

		# for each cycle...
		for cycle in range(common_cycle_len):
			inequality = False
			
			# ...print each wire with a different value in the two traces
			for wire_index in range(wire_count):
				if t1_objs[wire_index][cycle] != t2_objs[wire_index][cycle] and not (t1_objs[wire_index][cycle] == 8 and t2_objs[wire_index][cycle] == 32):
					if not inequality: # only print cycle number if there are differences in that cycle, and only once
						inequality = True
						print(f"Cycle #{cycle}:", file=file)
					print(f"\t{wire_names[wire_index]}: {t1_objs[wire_index][cycle]} vs {t2_objs[wire_index][cycle]}", file=file)
					diffs = True
		
		# print if there are no differences to rule out any bugs that would incorrectly leave the file empty
		if not diffs: 
			print("No differences found.", file=file)


# print all the differences between each wire in trace1 and trace2 for every cycle, accounting for offset in the section under test
# this lets you see the true differences in two squishtest traces with different distances between i1 and i2
def print_all_diffs_offset(start=0, offset=1, length=0, file=stdout):
	with open('differences_offset.txt', 'w') as file:
		diffs = False

		trace1_cycle_len = len(t1_objs[0])
		trace2_cycle_len = len(t2_objs[0])
		common_cycle_len = min(trace1_cycle_len, trace2_cycle_len)
		wire_count = len(t1_objs)

		# print comparison for each wire in each trace up to the start point
		for cycle in range(min(common_cycle_len, start)):
			inequality = False
			for wire_index in range(wire_count):
				if t1_objs[wire_index][cycle] != t2_objs[wire_index][cycle]:
					if not inequality:
						inequality = True
						print(f"Cycle #{cycle}:", file=file)
					print(f"\t{wire_names[wire_index]}: {t1_objs[wire_index][cycle]} vs {t2_objs[wire_index][cycle]}", file=file)
					diffs = True

		# print the offset segments of traces 1 and 2
		for cycle in range(start, min(common_cycle_len - offset, start + length - 1)):
			inequality = False
			for wire_index in range(wire_count):
				if t1_objs[wire_index][cycle] != t2_objs[wire_index][cycle+offset]:
					if not inequality:
						inequality = True
						print(f"Cycle #{cycle}, {cycle+offset}:", file=file)
					print(f"\t{wire_names[wire_index]}: {t1_objs[wire_index][cycle]} vs {t2_objs[wire_index][cycle+offset]}", file=file)
					diffs = True

		# for every value in the wire in each trace after the end point
		for cycle in range(start + length + offset, common_cycle_len):
			inequality = False
			for wire_index in range(wire_count):
				if t1_objs[wire_index][cycle] != t2_objs[wire_index][cycle]:
					if not inequality:
						inequality = True
						print(f"Cycle #{cycle}:", file=file)
					print(f"\t{wire_names[wire_index]}: {t1_objs[wire_index][cycle]} vs {t2_objs[wire_index][cycle]}", file=file)
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


# compare wires that share a prefix between traces for every cycle
def print_wire_2_prefix(wire_name, file=stdout):
	if file != stdout:
		file = open(file, 'w')
	
	filtered_objs1 = []
	filtered_objs2 = []
	filtered_wire_names = []
	for wn in wire_names:
		if wn.find(wire_name) == 0:
			filtered_wire_names.append(wn)
			filtered_objs1.append(t1_objs[wire_names.index(wn)])
			filtered_objs2.append(t2_objs[wire_names.index(wn)])
	
	# for every value in the wire in each trace, print their values and if they're the same or not
	for i in range(len(filtered_objs1[0])):
		print(f"#{i}:", file=file)
		for j in range(len(filtered_wire_names)):
			if filtered_objs1[j][i] == filtered_objs2[j][i]:
				print(f"\t{filtered_wire_names[j]} (same) = {filtered_objs1[j][i]}", file=file)
			else:
				print(f"\t{filtered_wire_names[j]} (diff) = {filtered_objs1[j][i]} vs {filtered_objs2[j][i]}", file=file)

	if file != stdout:
		file.close()


# compare a single wire between offset traces for every cycle
def print_wire_2_offset(wire_name, start=0, offset=1, length=0, file=stdout):
	if file != stdout:
		file = open(file, 'w')
	
	vals1 = t1_objs[wire_names.index(wire_name)]
	vals2 = t2_objs[wire_names.index(wire_name)]

	# for every value in the wire in each trace up to the start point
	for i in range(min(len(vals1), len(vals2), start)):
		if vals1[i] == vals2[i]:
			print(f"#{i}: {wire_name} (same) = {vals1[i]}", file=file)
		else:
			print(f"#{i}: {wire_name} (diff) = {vals1[i]} vs {vals2[i]}", file=file)
	
	# print the leading extra for trace 2
	for i in range(start, min(len(vals1), len(vals2), start + offset)):
		print(f"#{i}: {wire_name} (trace 2) = {vals2[i]}", file=file)

	# print the offset segments of traces 1 and 2
	for i in range(start, min(len(vals1) - offset, len(vals2) - offset, start + length - 1)):
		if vals1[i] == vals2[i+offset]:
			print(f"#{i}, {i+offset}: {wire_name} (same) = {vals1[i]}", file=file)
		else:
			print(f"#{i}, {i+offset}: {wire_name} (diff) = {vals1[i]} vs {vals2[i+offset]}", file=file)

	# print the trailing extra for trace 1
	for i in range(start + length, min(len(vals1), len(vals2), start + length + offset)):
		print(f"#{i}: {wire_name} (trace 1) = {vals1[i]}", file=file)

	# for every value in the wire in each trace after the end point
	for i in range(start + length + offset, min(len(vals1), len(vals2))):
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
