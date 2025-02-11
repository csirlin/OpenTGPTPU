import pickle
from sys import stdout
import pyrtl


# load pyrtl trace from pickle file
with open('../rw_mmc_empty_no_s_4m_10d/trace.pkl', 'rb') as file:
	sim_trace = pickle.load(file)

# get all the non-const wire names
wires = set()
for wn in sim_trace.trace:
	if wn.find('const') != 0:
		wires.add(wn)

# load all the wires into objs
# objs[i][j] is the value of wire i (in alphabetical order) at cycle j
wire_names = sorted(list(wires))
objs = []
for wn in wire_names:
	objs.append(sim_trace.trace[wn])


# print the values of wire_name for each cycle
def print_wire_1(wire_name, file=stdout):
	if file != stdout:
		file = open(file, 'w')

	vals = objs[wire_names.index(wire_name)]
	for i in range(len(vals)):
		print(f"#{i}: {wire_name} = {vals[i]}", file=file)

	if file != stdout:
		file.close()


# print the values of all wires that match a given prefix for each cycle
def print_wire_prefix(wire_prefix, file=stdout):
	if file != stdout:
		file = open(file, 'w')

	# filter out wires that don't have the prefix
	filtered_objs = []
	filtered_wire_names = []
	for wn in wire_names:
		if wn.find(wire_prefix) == 0:
			filtered_wire_names.append(wn)
			filtered_objs.append(objs[wire_names.index(wn)])

	# print the values of the filtered wires for each cycle 
	for i in range(len(filtered_objs[0])):
		print(f"#{i}:", file=file)
		for j in range(len(filtered_wire_names)):
			print(f"\t{filtered_wire_names[j]} = {filtered_objs[j][i]}", file=file)
			
	if file != stdout:
		file.close()


# print changes in wire values between consecutive cycles
def print_cycle_diff(file=stdout):
	if file != stdout:
		file = open(file, 'w')

	# iterate through each cycle
	for cycle in range(1, len(objs[0])):
		print(f"Cycle {cycle-1} -> {cycle}:", file=file)
		print(cycle, end = ' ') # log progress to console
		
		# go through each wire value and print if it has changed
		for w_index, wn in enumerate(wire_names):	
			if objs[w_index][cycle] != objs[w_index][cycle-1]: 
				print(f"\t{wn}: {objs[wire_names.index(wn)][cycle-1]} -> {objs[wire_names.index(wn)][cycle]}", file=file)
	
	if file != stdout:
		file.close()


# find all the unique wires that change between cycles start and end
def find_changed_wires(start, end, file=stdout):
	
	# go through each cycle change (from start -> start+1 to end-1 -> end) 
	# and create a set of unique wires that change
	changed_wires = set()
	for cycle in range(start, end):
		for w_index, wn in enumerate(wire_names):
			if objs[w_index][cycle] != objs[w_index][cycle+1]:
				changed_wires.add(wn)
	
	if file != stdout:
		file = open(file, 'w')

	# print the changed wires
	for wn in sorted(list(changed_wires)):
		print(wn, file=file)

	if file != stdout:
		file.close()
