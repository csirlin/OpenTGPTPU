# specify hostmem and weight matrices for branch_eq_pyrtl test
import numpy as np

def store():

    hm = np.arange(64).reshape(8, 8)
    w0 = np.arange(64).reshape(8, 8)
    w = np.zeros((1, 8, 8))
    w[0] = w0
    
    np.save('hm_8x8', hm.astype(np.int32))
    np.save('w_8x8', w.astype(np.int32))

store()