import glob
import subprocess

# transfer tests from matmuls-r-us to mullifier_examples
# run from OpenTGPTPU as current directory

filepaths = glob.glob("../matmuls-r-us/test/*.mlir")
filenames = [filepath.split("/")[-1].split(".")[0] for filepath in filepaths]
for i in range(len(filenames)):
    if filenames[i] in ["alloc", "direct_branch", "loop_sum", "simple_alloc"]:
        print(f"skipping {filenames[i]} to avoid gpmatmul compiler error")
        continue
    print(filenames[i], filepaths[i])
    subprocess.run(["mkdir", f"test/mullifier_examples/test_{filenames[i]}"])
    subprocess.run(["../matmuls-r-us/build/bin/gpmatmul-opt", filepaths[i]])
    subprocess.run(["python", "../matmuls-r-us/generate_input.py"])
    subprocess.run(["python", "../matmuls-r-us/tile_gen.py"])
    subprocess.run(["mv", "input.npy", "weights.npy" , "open_tpu.a", 
                    f"test/mullifier_examples/test_{filenames[i]}/"])
    subprocess.run(["python", "assembler.py", 
                    f"test/mullifier_examples/test_{filenames[i]}/open_tpu.a"])
    

