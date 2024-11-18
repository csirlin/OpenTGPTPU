# specify weights for test_rw
# hostmem doesn't matter as there are no matmul instructions, although dummy hostmem still has to be generated and loaded
import numpy as np

def store():

    hm = np.zeros((3*8, 8))


    wm = np.zeros((5, 8, 8))

    for i in range(5):
        for j in range(8):
            for k in range(8):
                wm[i][j][k] = 16*i + j + 1


    np.save('input', hm.astype(np.int32))
    np.save('weights', wm.astype(np.int32))

store()