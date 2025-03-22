#!/usr/bin/env python
# Required versions:
# Python 3.8.18
# PyRTL 0.8.6

import random
import subprocess
import os, shutil
import time
import numpy as np

# Import our generate.py module for creating memory files.
import generate

# ----------------------------- ADJUSTABLE PARAMETERS -----------------------------

# MATRIX_DIM should be one of {4, 8, 16}. Determines the matrix (tile) dimensions.
MATRIX_DIM = 8             # For example, use 8x8 matrices. (Change to 4 or 16 as needed.)
BITWIDTH = 32              # Data bitwidth.
NUM_RANDOM_INSTR_MIN = 5   # Minimum number of random instructions (after preload).
NUM_RANDOM_INSTR_MAX = 20  # Maximum number of random instructions.
TEST_DIR = "fuzz_test_dir" # Directory for generated test files.

# Derived parameters based on MATRIX_DIM:
NUM_TILES = 8                      # Number of tiles for host memory.
HOST_ROWS = NUM_TILES * MATRIX_DIM # Total rows in host memory.
NUM_WEIGHTS = 8                    # Number of weight matrices.
UB_MAX = HOST_ROWS                 # We restrict UB addresses to be within host memory size.
ACC_CAPACITY = HOST_ROWS           # Set accumulator size equal to host memory size.

# Number of test sets to generate.
NUM_TEST_SETS = 100

# Allowed operations.
ALLOWED_OPS = ['RHM', 'WHM', 'RW', 'MMC', 'ACT']

# ----------------------------- FIFO COUNTER MANAGEMENT -----------------------------
# The FIFO counter tracks the number of weights in the FIFO (range 0-4).
# RW increments the counter; MMC with switch flag decrements the counter.
fifo_count = 0  # Start with an empty FIFO.

# ----------------------------- RANDOM INSTRUCTION GENERATION -----------------------------

def generate_random_instruction():
    """
    Generate a random instruction string based on the current FIFO count.
    - If fifo_count == 0, MMC is disallowed.
    - If fifo_count == 4, RW is disallowed.
    Updates the global fifo_count accordingly.
    """
    global fifo_count

    # Build a list of possible operations given the FIFO constraints.
    possible_ops = ALLOWED_OPS.copy()
    if fifo_count == 0:
        if 'MMC' in possible_ops:
            possible_ops.remove('MMC')
    if fifo_count == 4:
        if 'RW' in possible_ops:
            possible_ops.remove('RW')
    
    op = random.choice(possible_ops)
    args = []
    
    if op in ['RHM', 'WHM']:
        # Format: "OP SRC, TAR, LEN" (WITH spaces after commas)
        length = random.randint(1, MATRIX_DIM)
        hm = random.randint(0, HOST_ROWS - length)
        ub = random.randint(0, UB_MAX - length)
        args = [str(hm), str(ub), str(length)]
    
    elif op == 'RW':
        # Format: "RW 0xab" (weight index in hex)
        weight = random.randint(0, NUM_WEIGHTS - 1)
        args = [hex(weight)]
    
    elif op == 'MMC':
        # Format: "MMC[flags] ACC, UB, LEN" (WITH spaces after commas)
        o_flag = random.choice([True, False])
        s_flag = random.choice([True, False])
        flag_str = ""
        if o_flag:
            flag_str += ".O"
        if s_flag:
            flag_str += ".S"
        length = random.randint(1, MATRIX_DIM)
        acc = random.randint(0, ACC_CAPACITY - length)
        ub = random.randint(0, UB_MAX - length)
        op = op + flag_str  # Append flags
        args = [str(acc), str(ub), str(length)]
        if s_flag:
            fifo_count = max(0, fifo_count - 1)  # Decrement FIFO count if switch flag is on
    
    elif op == 'ACT':
        # Format: "ACT FUNC, UB, LEN" (WITH spaces after commas)
        func = random.choice([0x1, 0x2])
        length = random.randint(1, MATRIX_DIM)
        ub = random.randint(0, UB_MAX - length)
        args = [hex(func), str(ub), str(length)]
    
    # Return instruction in the format that works with the assembler (WITH spaces after commas)
    if args:
        return f"{op} " + ", ".join(args)
    else:
        return op

def generate_random_program():
    """
    Generates a random test program:
      - Prepend a series of RHM preload instructions, one for each tile.
      - Append a random number of additional instructions generated with FIFO constraints.
      - Append a final HLT instruction.
    """
    # Preload instructions: one per tile.
    preload_instructions = []
    for i in range(NUM_TILES):
        start = i * MATRIX_DIM
        preload_instructions.append(f"RHM {start}, {start}, {MATRIX_DIM}")
    
    # Reset FIFO count after preloading (assume FIFO is empty after preloads).
    global fifo_count
    fifo_count = 0

    num_random = random.randint(NUM_RANDOM_INSTR_MIN, NUM_RANDOM_INSTR_MAX)
    random_instructions = [generate_random_instruction() for _ in range(num_random)]
    
    program = preload_instructions + random_instructions + ["HLT"]
    return program

# ----------------------------- FILE AND EXTERNAL TOOL HELPERS -----------------------------

def remove_existing_files(directory):
    """Removes all files and directories in the given directory."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def write_program_to_file(instructions, filename):
    """Writes the instructions (one per line) to the given file."""
    with open(filename, 'w') as f:
        for instr in instructions:
            f.write(instr + "\n")

def assemble_program(asm_file, binary_file):
    """
    Calls the assembler to convert the assembly file to a binary.
    The assembler expects the source file as its only argument.
    """
    cmd = ["python", "assembler.py", asm_file]
    subprocess.run(cmd, check=True)

def run_simulation(binary_file, hostmem_file, dram_file, simulator, output_folder):
    """
    Runs one of the simulators on the given binary file.
    Args:
        binary_file: Path to the assembled binary file
        hostmem_file: Path to host memory file
        dram_file: Path to weights file
        simulator: Either "sim" or "runtpu"
        output_folder: Folder where simulator should save output files
    """
    if simulator == "sim":
        cmd = ["python", "sim.py", binary_file, hostmem_file, dram_file, "-f", output_folder]
    elif simulator == "runtpu":
        cmd = ["python", "runtpu.py", binary_file, hostmem_file, dram_file, "-f", output_folder]
    else:
        raise ValueError("Unknown simulator specified")
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout

def load_output_array(folder, name):
    """Loads the .npy file from the specified folder."""
    return np.load(os.path.join(folder, name))

def compare_sim_outputs(sim_folder, runtpu_folder):
    """
    Compares the host memory arrays produced by sim.py and runtpu.py.
    You can expand this to compare other arrays if needed.
    """
    sim_host = load_output_array(sim_folder, "sim_hostmem.npy")
    runtpu_host = load_output_array(runtpu_folder, "runtpu_hostmem.npy")
    return np.array_equal(sim_host, runtpu_host)

# ----------------------------- MAIN FUZZER ROUTINE -----------------------------

def main():
    # Create and clear test directory
    os.makedirs(TEST_DIR, exist_ok=True)
    remove_existing_files(TEST_DIR)
    
    # Create new folder structure
    success_dir = os.path.join(TEST_DIR, "success")
    fail_dir = os.path.join(TEST_DIR, "fail")
    error_dir = os.path.join(TEST_DIR, "fuzzer_error")
    
    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(fail_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)
    
    # Generate fresh host and weights memory files using generate.py
    hostmem_file = generate.make_hostmem(TEST_DIR, MATRIX_DIM, BITWIDTH, NUM_TILES)
    weights_file = generate.make_weights(TEST_DIR, MATRIX_DIM, BITWIDTH, NUM_WEIGHTS)
    
    # Run multiple test sets
    for i in range(NUM_TEST_SETS):
        # Generate a random test program
        program = generate_random_program()
        test_id = f"test_{int(time.time())}_{i}"
        
        print(f"\n=== Test Set {i+1}/{NUM_TEST_SETS} (ID: {test_id}) ===")
        
        # Create test files
        asm_file = os.path.join(TEST_DIR, f"{test_id}.a")
        binary_file = os.path.join(TEST_DIR, f"{test_id}.out")
        write_program_to_file(program, asm_file)
        
        # Define output folders for simulators
        sim_output_folder = os.path.join(TEST_DIR, f"{test_id}_sim")
        runtpu_output_folder = os.path.join(TEST_DIR, f"{test_id}_runtpu")
        os.makedirs(sim_output_folder, exist_ok=True)
        os.makedirs(runtpu_output_folder, exist_ok=True)
        
        # Assemble the program
        print("Assembling program...")
        try:
            assemble_program(asm_file, binary_file)
        except subprocess.CalledProcessError as e:
            print(f"Assembly failed: {e}")
            
            # Create error directory for this test
            test_error_dir = os.path.join(error_dir, f"{test_id}_assembly_error")
            os.makedirs(test_error_dir, exist_ok=True)
            
            # Save program and error info
            error_file = os.path.join(test_error_dir, "error.txt")
            with open(error_file, "w") as f:
                f.write(f"Assembly error:\n{str(e)}\n\n")
                if hasattr(e, 'stderr'):
                    f.write(f"Error output:\n{e.stderr}\n\n")
                f.write("Assembly file contents:\n")
                with open(asm_file, "r") as asm_f:
                    f.write(asm_f.read())
            
            # Copy assembly file to error directory
            shutil.copy2(asm_file, os.path.join(test_error_dir, f"{test_id}.a"))
            
            # Clean up temporary files
            os.remove(asm_file)
            continue
        
        # Run sim.py
        try:
            sim_output = run_simulation(
                binary_file, hostmem_file, weights_file, 
                simulator="sim", output_folder=sim_output_folder
            )
            print("Ran sim.py successfully")
        except subprocess.CalledProcessError as e:
            print(f"sim.py failed: {e}")
            
            # Create error directory for this test
            test_error_dir = os.path.join(error_dir, f"{test_id}_sim_error")
            os.makedirs(test_error_dir, exist_ok=True)
            
            # Save program and error info
            error_file = os.path.join(test_error_dir, "error.txt")
            with open(error_file, "w") as f:
                f.write(f"sim.py error:\n{str(e)}\n\n")
                if hasattr(e, 'output'):
                    f.write(f"Output:\n{e.output}\n\n")
                if hasattr(e, 'stderr'):
                    f.write(f"Error output:\n{e.stderr}\n\n")
                f.write("Assembly file contents:\n")
                with open(asm_file, "r") as asm_f:
                    f.write(asm_f.read())
            
            # Copy files to error directory
            shutil.copy2(asm_file, os.path.join(test_error_dir, f"{test_id}.a"))
            shutil.copy2(binary_file, os.path.join(test_error_dir, f"{test_id}.out"))
            
            # Clean up temporary files
            os.remove(asm_file)
            os.remove(binary_file)
            shutil.rmtree(sim_output_folder)
            shutil.rmtree(runtpu_output_folder)
            continue
        
        # Run runtpu.py
        try:
            runtpu_output = run_simulation(
                binary_file, hostmem_file, weights_file, 
                simulator="runtpu", output_folder=runtpu_output_folder
            )
            print("Ran runtpu.py successfully")
        except subprocess.CalledProcessError as e:
            print(f"runtpu.py failed: {e}")
            
            # Create error directory for this test
            test_error_dir = os.path.join(error_dir, f"{test_id}_runtpu_error")
            os.makedirs(test_error_dir, exist_ok=True)
            
            # Save program and error info
            error_file = os.path.join(test_error_dir, "error.txt")
            with open(error_file, "w") as f:
                f.write(f"runtpu.py error:\n{str(e)}\n\n")
                if hasattr(e, 'output'):
                    f.write(f"Output:\n{e.output}\n\n")
                if hasattr(e, 'stderr'):
                    f.write(f"Error output:\n{e.stderr}\n\n")
                f.write("Assembly file contents:\n")
                with open(asm_file, "r") as asm_f:
                    f.write(asm_f.read())
            
            # Copy files to error directory
            shutil.copy2(asm_file, os.path.join(test_error_dir, f"{test_id}.a"))
            shutil.copy2(binary_file, os.path.join(test_error_dir, f"{test_id}.out"))
            
            # If sim.py ran successfully, save its output too
            if os.path.exists(sim_output_folder):
                sim_files = os.listdir(sim_output_folder)
                for file in sim_files:
                    src = os.path.join(sim_output_folder, file)
                    dst = os.path.join(test_error_dir, file)
                    shutil.copy2(src, dst)
            
            # Clean up temporary files
            os.remove(asm_file)
            os.remove(binary_file)
            shutil.rmtree(sim_output_folder)
            shutil.rmtree(runtpu_output_folder)
            continue
        
        # Compare outputs (host memory arrays)
        try:
            outputs_match = compare_sim_outputs(sim_output_folder, runtpu_output_folder)
            
            if outputs_match:
                print("TEST PASSED: Outputs match")
                
                # Move instruction files to success directory
                success_test_dir = os.path.join(success_dir, test_id)
                os.makedirs(success_test_dir, exist_ok=True)
                
                # Copy assembly file and binary file
                shutil.copy2(asm_file, os.path.join(success_test_dir, f"{test_id}.a"))
                shutil.copy2(binary_file, os.path.join(success_test_dir, f"{test_id}.out"))
                
                # Clean up temporary files (don't need the outputs for successful tests)
                os.remove(asm_file)
                os.remove(binary_file)
                shutil.rmtree(sim_output_folder)
                shutil.rmtree(runtpu_output_folder)
            else:
                print("TEST FAILED: Outputs differ")
                
                # Create fail directory for this test
                fail_test_dir = os.path.join(fail_dir, test_id)
                os.makedirs(fail_test_dir, exist_ok=True)
                
                # Copy all relevant files
                shutil.copy2(asm_file, os.path.join(fail_test_dir, f"{test_id}.a"))
                shutil.copy2(binary_file, os.path.join(fail_test_dir, f"{test_id}.out"))
                
                # Copy simulator outputs
                sim_files = os.listdir(sim_output_folder)
                for file in sim_files:
                    src = os.path.join(sim_output_folder, file)
                    dst = os.path.join(fail_test_dir, file)
                    shutil.copy2(src, dst)
                
                runtpu_files = os.listdir(runtpu_output_folder)
                for file in runtpu_files:
                    src = os.path.join(runtpu_output_folder, file)
                    dst = os.path.join(fail_test_dir, file)
                    shutil.copy2(src, dst)
                
                # Clean up temporary files
                os.remove(asm_file)
                os.remove(binary_file)
                shutil.rmtree(sim_output_folder)
                shutil.rmtree(runtpu_output_folder)
        
        except Exception as e:
            print(f"Error comparing outputs: {e}")
            
            # Create error directory for this test
            test_error_dir = os.path.join(error_dir, f"{test_id}_comparison_error")
            os.makedirs(test_error_dir, exist_ok=True)
            
            # Save error info
            error_file = os.path.join(test_error_dir, "error.txt")
            with open(error_file, "w") as f:
                f.write(f"Error comparing outputs:\n{str(e)}\n\n")
                f.write("Assembly file contents:\n")
                with open(asm_file, "r") as asm_f:
                    f.write(asm_f.read())
            
            # Copy all files
            shutil.copy2(asm_file, os.path.join(test_error_dir, f"{test_id}.a"))
            shutil.copy2(binary_file, os.path.join(test_error_dir, f"{test_id}.out"))
            
            # Try to copy simulator outputs if they exist
            if os.path.exists(sim_output_folder):
                sim_files = os.listdir(sim_output_folder)
                for file in sim_files:
                    src = os.path.join(sim_output_folder, file)
                    dst = os.path.join(test_error_dir, file)
                    shutil.copy2(src, dst)
            
            if os.path.exists(runtpu_output_folder):
                runtpu_files = os.listdir(runtpu_output_folder)
                for file in runtpu_files:
                    src = os.path.join(runtpu_output_folder, file)
                    dst = os.path.join(test_error_dir, file)
                    shutil.copy2(src, dst)
            
            # Clean up temporary files
            os.remove(asm_file)
            os.remove(binary_file)
            shutil.rmtree(sim_output_folder)
            shutil.rmtree(runtpu_output_folder)
    
    print("\nAll test sets completed.")
    
    # Print summary
    success_count = len([d for d in os.listdir(success_dir) if os.path.isdir(os.path.join(success_dir, d))])
    fail_count = len([d for d in os.listdir(fail_dir) if os.path.isdir(os.path.join(fail_dir, d))])
    error_count = len([d for d in os.listdir(error_dir) if os.path.isdir(os.path.join(error_dir, d))])
    
    print(f"\nTest Summary:")
    print(f"  Successful tests: {success_count}")
    print(f"  Failed tests:     {fail_count}")
    print(f"  Errors:           {error_count}")
    print(f"  Total:            {success_count + fail_count + error_count}")
    
    # Check no stray files left in test directory
    stray_files = [f for f in os.listdir(TEST_DIR) 
                  if f not in ["success", "fail", "fuzzer_error", "hostmem.npy", "weights.npy"]]
    if stray_files:
        print(f"\nWarning: {len(stray_files)} stray files found in {TEST_DIR}:")
        for f in stray_files:
            print(f"  {f}")
    else:
        print(f"\nNo stray files in {TEST_DIR}.")

if __name__ == "__main__":
    main()
