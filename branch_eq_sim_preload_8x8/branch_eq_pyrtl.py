# specify hostmem and weight matrices for branch_eq_pyrtl test
import numpy as np

def store():

    hm = np.zeros((3*8, 8))

    # no data, blank control
    hm0   = [ [  0,  0,  0,  0,  0,  0,  0,  1  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ] ]

    # starting data
    hm1   = [ [-10,  0,  0,  0,  0,  0,  0,  1  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ] ]
    
    # increment
    hm2   = [ [  1,  2,  3,  4,  0,  0,  0,  0  ],
              [  2,  4,  6,  8,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ] ]
    
    
    
    hm[0:8, 0:8] = hm0
    hm[8:16, 0:8] = hm1
    hm[16:24, 0:8] = hm2
    
    w = np.zeros((3, 8, 8))

    # data = I, ctrl = branch + 250
    w[0] =  [ [  1,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  1,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  1,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  1,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  1, 44,  1,  1  ] ]
    # [-1][-1] = 1
    # [-1][-2]: branch enable (0 or 1)
    # [-1][-3]: LSByte of branch amt
    # [-1][-4]: MSByte of branch amt (for 12 bit PC only 4 LSb's of this are used)
    
    # data = I, ctrl = 0
    w[1] =  [ [  1,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  1,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  1,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  1,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  1  ] ]
    
    # data = 0, ctrl = branch - 300
    w[2] =  [ [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0,  0,  0,  0,  0  ],
              [  0,  0,  0,  0, -1,  6,  1,  1  ] ]
    
    np.save('branch_eq_pyrtl_input', hm.astype(np.int32))
    np.save('branch_eq_pyrtl_weights', w.astype(np.int32))

store()