# generate inputs and weights for squish testing
import numpy as np
import os

def get_weight_filename(path, bitwidth, matsize):
    return os.path.join(path, f"weights_{bitwidth}b_{matsize}m.npy")

def get_hostmem_filename(path, bitwidth, matsize):
    return os.path.join(path, f"hostmem_{bitwidth}b_{matsize}m.npy")


def make_weights(path, matsize, bitwidth, num_weights):
    weights_filepath = get_weight_filename(path, bitwidth, matsize)
    if (os.path.exists(weights_filepath)):
        return weights_filepath
    
    f = open("weights.txt", "w")
    os.makedirs(path, exist_ok=True)
    weights = np.zeros((num_weights, matsize, matsize))
    for i in range(num_weights):
        weights[i] = np.arange(i * matsize**2 + 1, (i+1)*matsize**2 + 1).reshape(matsize, matsize)        
    np.save(weights_filepath, weights.astype(np.int32))
    print(f"make_weights result is {weights}", file=f)
    return weights_filepath

def make_hostmem(path, matsize, bitwidth, num_tiles):
    hostmem_filepath = get_hostmem_filename(path, bitwidth, matsize)
    if (os.path.exists(hostmem_filepath)):
        return hostmem_filepath
    
    f = open("hostmem.txt", "w")
    os.makedirs(path, exist_ok=True)
    hostmem = np.arange(1, num_tiles * matsize**2 + 1).reshape(num_tiles * matsize, matsize)
    np.save(hostmem_filepath, hostmem.astype(np.int32))
    print(f"make_hostmem result is {hostmem}", file=f)
    return hostmem_filepath
