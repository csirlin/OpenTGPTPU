# specify hostmem and weight matrices for branch_eq_pyrtl test
import numpy as np

def store():

    hm = np.arange(256).reshape(16, 16)
    w0 = np.arange(256).reshape(16, 16)
    w = np.zeros((1, 16, 16))
    w[0] = w0
    
    np.save('hm_16x16', hm.astype(np.int32))
    np.save('w_16x16', w.astype(np.int32))

store()