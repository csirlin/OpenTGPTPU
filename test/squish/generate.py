# generate inputs and weights for squish testing
import numpy as np
import os

def make_weights(path, matsize, bitwidth, num_weights):
    os.makedirs(path, exist_ok=True)
    weights = np.zeros((num_weights, matsize, matsize))
    for i in range(num_weights):
        weights[i] = np.arange(i * matsize**2 + 1, (i+1)*matsize**2 + 1).reshape(matsize, matsize)
    weights_filepath = os.path.join(path, f"weights_{bitwidth}b_{matsize}x{matsize}.npy")
    np.save(weights_filepath, weights.astype(np.int32))
    return weights_filepath

def make_hostmem(path, matsize, bitwidth, num_tiles):
    os.makedirs(path, exist_ok=True)
    hostmem = np.arange(1, num_tiles * matsize**2 + 1).reshape(matsize, num_tiles * matsize)
    hostmem_filepath = os.path.join(path, f"hostmem_{bitwidth}b_{matsize}x{matsize}.npy")
    np.save(hostmem_filepath, hostmem.astype(np.int32))
    return hostmem_filepath
