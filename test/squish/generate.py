# generate inputs and weights for squish testing
import numpy as np
import os

def make_weights(path, matsize, bitwidth, num_weights):
    f = open("weights.txt", "w")
    os.makedirs(path, exist_ok=True)
    weights = np.zeros((num_weights, matsize, matsize))
    for i in range(num_weights):
        weights[i] = np.arange(i * matsize**2 + 1, (i+1)*matsize**2 + 1).reshape(matsize, matsize)
    weights_filepath = os.path.join(path, f"weights_{bitwidth}b_{matsize}x{matsize}.npy")
    np.save(weights_filepath, weights.astype(np.int32))
    print(f"make_weights result is {weights}", file=f)
    return weights_filepath

def make_hostmem(path, matsize, bitwidth, num_tiles):
    f = open("hostmem.txt", "w")
    os.makedirs(path, exist_ok=True)
    hostmem = np.arange(1, num_tiles * matsize**2 + 1).reshape(num_tiles * matsize, matsize)
    hostmem_filepath = os.path.join(path, f"hostmem_{bitwidth}b_{matsize}x{matsize}.npy")
    np.save(hostmem_filepath, hostmem.astype(np.int32))
    print(f"make_hostmem result is {hostmem}", file=f)
    return hostmem_filepath
