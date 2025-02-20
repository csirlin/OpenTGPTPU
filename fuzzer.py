import random
import subprocess
import os, shutil
import time

# Import our generate.py module for creating memory files.
import generate

# ----------------------------- ADJUSTABLE PARAMS -----------------------------

# MATRIX_DIM should be one of {4, 8, 16}. This determines the width (and height) of each matrix.
MATRIX_DIM = 8             # For example, use 8x8 matrices. You can change this to 4 or 16.
BITWIDTH = 32              # Data bitwidth.
NUM_RANDOM_INSTR_MIN = 5   # Minimum number of random instructions (after preload).
NUM_RANDOM_INSTR_MAX = 20  # Maximum number of random instructions.
TEST_DIR = "fuzz_test_dir" # Directory for generated test files.

# Derived parameters based on MATRIX_DIM:

NUM_TILES = 8                      # Number of tiles for host memory.
HOST_ROWS = NUM_TILES * MATRIX_DIM # Total rows in host memory.
NUM_WEIGHTS = 8                    # Number of weight matrices.
UB_MAX = HOST_ROWS                 # For the unified buffer we restrict addresses to a small subset            
ACC_CAPACITY = 4000                # For the accumulator, we assume its capacity is 4000 rows.

# Number of test sets to generate (e.g., 100)
NUM_TEST_SETS = 100



# Allowed operations (HLT will be appended; NOP is not used).
OPERATIONS = {
    'RHM': 3,
    'WHM': 3,
    'RW':  1,
    'MMC': 3,
    'ACT': 3,
}

# For MMC instructions, define allowed flag options.
MMC_FLAGS = ['', '.O', '.S']


#  ----------------------------- Random Instruction Generation -----------------------------

def generate_random_instruction():
    
    # Randomly selects one of the allowed operations and generates an instruction string
    
    op = random.choice(list(OPERATIONS.keys()))
    # Do not generate HLT here; it will be appended at the end.
    args = []
    
    if op in ['RHM', 'WHM']:
        # Format: "OP SRC, TAR, LEN"
        length = random.randint(1, MATRIX_DIM)
        # Ensure HM address + length is within HOST_ROWS.
        hm = random.randint(0, HOST_ROWS - length)
        # For unified buffer, we restrict UB to [0, UB_MAX - length].
        ub = random.randint(0, UB_MAX - length)
        args = [str(hm), str(ub), str(length)]
    
    elif op == 'RW':
        # Format: "RW 0xab" - weight index in hex.
        weight = random.randint(0, NUM_WEIGHTS - 1)
        args = [hex(weight)]
    
    elif op == 'MMC':
        # Format: "MMC[flag] ACC, UB, LEN"
        length = random.randint(1, MATRIX_DIM)
        # ACC address: ensure ACC + length is within ACC_CAPACITY.
        acc = random.randint(0, ACC_CAPACITY - length)
        ub = random.randint(0, UB_MAX - length)
        flag = random.choice(MMC_FLAGS)
        op = op + flag  # Append flag to opcode.
        args = [str(acc), str(ub), str(length)]
    
    elif op == 'ACT':
        # Format: "ACT FUNC, UB, LEN"
        length = random.randint(1, MATRIX_DIM)
        # ACC address: ensure ACC + length is within ACC_CAPACITY.
        acc = random.randint(0, ACC_CAPACITY - length)
        ub = random.randint(0, UB_MAX - length)
        args = [hex(0), str(ub), str(length)]
    
    # Return instruction in the required format with commas separating operands.
    if args:
        return f"{op} " + ", ".join(args)
    else:
        return op

def generate_random_program():
    
    # Generates a random test program.
    
    """ 
    - Prepend a couple of hardcoded RHM preload instructions (with comma-separated operands)
      so that some matrices are loaded into the Unified Buffer before random instructions run.
    - Append a final HLT instruction.
    """
    preload_instructions = [
        f"RHM 0, 0, {MATRIX_DIM}",                         # Preload: load a matrix from host to UB.
        f"RHM {MATRIX_DIM}, {MATRIX_DIM}, {MATRIX_DIM}",   # Another preload.
        f"RW {hex(random.randint(0, NUM_WEIGHTS - 1))}"    # Force-load one weight into the FIFO.
    ]
    
    num_random = random.randint(NUM_RANDOM_INSTR_MIN, NUM_RANDOM_INSTR_MAX)
    random_instructions = [generate_random_instruction() for _ in range(num_random)]
    
    program = preload_instructions + random_instructions + ["HLT"]
    return program


# ----------------------------- File and External Tool Helpers -----------------------------

def remove_existing_files(directory):
    #Removes the specified files from the directory if they exist.
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def write_program_to_file(instructions, filename):
    # Writes the list of instruction strings to a file, one per line.
    with open(filename, 'w') as f:
        for instr in instructions:
            f.write(instr + "\n")

def assemble_program(asm_file, binary_file):
    # Calls the assembler to convert the assembly file into a binary file.

    cmd = ["python", "assembler.py", asm_file]
    subprocess.run(cmd, check=True)

def run_simulation(binary_file, hostmem_file, dram_file, simulator="sim"):

    # Runs one of the simulators on the given binary.
    # The command-line formats for sim.py and runtpu.py remain the same.
    
    if simulator == "sim":
        cmd = ["python3", "sim.py", binary_file, hostmem_file, dram_file]
    elif simulator == "runtpu":
        cmd = ["python3", "runtpu_mod.py", binary_file, hostmem_file, dram_file]
    else:
        raise ValueError("Unknown simulator specified")
    
    # try:
    #     result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    #     return result.stdout
    # except subprocess.CalledProcessError as e:
    #     print(e.returncode)
    #     print(e.stdout)
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout
        
    

def compare_outputs(output1, output2):
    # compares outputs of random instruction set on both programs
    return output1.strip() == output2.strip()


# ----------------------------- Main Fuzzer Routine -----------------------------

def main():
    # Create test directory.
    os.makedirs(TEST_DIR, exist_ok=True)
    remove_existing_files(TEST_DIR)

    # Create subdirectories for results and errors.
    results_dir = os.path.join(TEST_DIR, "results")
    matched_dir = os.path.join(results_dir, "matched")
    differ_dir = os.path.join(results_dir, "differ")
    os.makedirs(matched_dir, exist_ok=True)
    os.makedirs(differ_dir, exist_ok=True)

    errors_dir = os.path.join(TEST_DIR, "errors")
    errors_sim_dir = os.path.join(errors_dir, "sim")
    errors_runtpu_dir = os.path.join(errors_dir, "runtpu")
    os.makedirs(errors_sim_dir, exist_ok=True)
    os.makedirs(errors_runtpu_dir, exist_ok=True)
    
    # Generate fresh host and weights memory files using generate.py.
    hostmem_file = generate.make_hostmem(TEST_DIR, MATRIX_DIM, BITWIDTH, NUM_TILES)
    weights_file = generate.make_weights(TEST_DIR, MATRIX_DIM, BITWIDTH, NUM_WEIGHTS)
    
    # # Generate the Random Test 
    # program = generate_random_program()
    # timestamp = int(time.time())
    # asm_file = os.path.join(TEST_DIR, f"fuzz_test_{timestamp}.a")
    # # The assembler produces a binary file with a ".out" extension.
    # binary_file = asm_file[:asm_file.rfind('.')] + ".out"
    
    # write_program_to_file(program, asm_file)
    
    # print("Generated program:")
    # for line in program:
    #     print("  ", line)
    
    # # Assemble the Program
    # print("\nAssembling program...")
    # assemble_program(asm_file, binary_file)
    

    # # Run the Simulators
    # print("\nRunning sim.py...")
    # sim_output = run_simulation(binary_file, hostmem_file, weights_file, simulator="sim")
    # print("Running runtpu.py...")
    # runtpu_output = run_simulation(binary_file, hostmem_file, weights_file, simulator="runtpu")
    
    
    # # Compare outputs.
    # if compare_outputs(sim_output, runtpu_output):
        # print("""\nTEST PASSED: Outputs match.
        #       (•_•)
        #       ( •_•)>⌐■-■
        #       (⌐■_■)""")
    # else:
    #     print("\nTEST FAILED: Outputs differ.")
    #     print('WAT (╯°□°）╯︵ ┻━┻')
    #     print("\n--- sim.py output ---")
    #     print(sim_output)
    #     print("\n--- runtpu.py output ---")
    #     print(runtpu_output)

    # Run a variable number of test sets.
    for i in range(NUM_TEST_SETS):
        # Generate a random test program.
        program = generate_random_program()
        unique_name = f"fuzz_test{i}"
        asm_file = os.path.join(TEST_DIR, unique_name + ".a")
        binary_file = asm_file[:asm_file.rfind('.')] + ".out"
        
        write_program_to_file(program, asm_file)
        print(f"\n=== Test Set {i+1} ===")
        print("Generated program:")
        for line in program:
            print("  ", line)
        
        # Assemble the program.
        print("Assembling program...")
        try:
            assemble_program(asm_file, binary_file)
        except subprocess.CalledProcessError as e:
            print(f"Assembly failed for {unique_name}. Skipping test set.")
            continue  # Skip this test set.
        
        # Run sim.py in a try-except block.
        try:
            sim_output = run_simulation(binary_file, hostmem_file, weights_file, simulator="sim")
        except subprocess.CalledProcessError as e:
            error_file = os.path.join(errors_sim_dir, unique_name + ".txt")
            with open(error_file, "w") as f:
                f.write("Error running sim.py:\n")
                f.write(str(e) + "\n")
                f.write("Output:\n" + e.output + "\n")
                f.write("Error Output:\n" + e.stderr + "\n")
                f.write("Assembly file contents:\n")
                with open(asm_file, "r") as asm_f:
                    f.write(asm_f.read())
            print(f"sim.py error logged to {error_file}. Skipping test set.")
            continue
        
        # Run runtpu_mod.py in a try-except block.
        try:
            runtpu_output = run_simulation(binary_file, hostmem_file, weights_file, simulator="runtpu")
        except subprocess.CalledProcessError as e:
            error_file = os.path.join(errors_runtpu_dir, unique_name + ".txt")
            with open(error_file, "w") as f:
                f.write("Error running runtpu_mod.py:\n")
                f.write(str(e) + "\n")
                f.write("Output:\n" + e.output + "\n")
                f.write("Error Output:\n" + e.stderr + "\n")
                f.write("Assembly file contents:\n")
                with open(asm_file, "r") as asm_f:
                    f.write(asm_f.read())
            print(f"runtpu_mod.py error logged to {error_file}. Skipping test set.")
            continue
        
        # Compare outputs if both simulators ran successfully.
        if compare_outputs(sim_output, runtpu_output):
            print("""\nTEST PASSED: Outputs match.
              (•_•)
              ( •_•)>⌐■-■
              (⌐■_■)""")
            # Move the assembly (.a) and binary (.out) files to the matched directory.
            shutil.move(asm_file, os.path.join(matched_dir, os.path.basename(asm_file)))
            shutil.move(binary_file, os.path.join(matched_dir, os.path.basename(binary_file)))
        else:
            print("TEST FAILED: Outputs differ.")
            print('WAT (╯°□°）╯︵ ┻━┻')
            # print("\n--- sim.py output ---")
            print(sim_output)
            # print("\n--- runtpu_mod.py output ---")
            print(runtpu_output)
            # Move the assembly (.a) and binary (.out) files to the differ directory.
            shutil.move(asm_file, os.path.join(differ_dir, os.path.basename(asm_file)))
            shutil.move(binary_file, os.path.join(differ_dir, os.path.basename(binary_file)))
    
    print("\nAll test sets completed.")

if __name__ == "__main__":
    main()

