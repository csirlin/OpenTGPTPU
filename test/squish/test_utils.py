# utilities for running squish tests


import os
import sys
from squishtest import squish_test

class Params:
    def __init__(self, instr1, instr2, bitwidth, matsize, use_nops, setup_rw_ct, 
                 base_distance, test_folder):
        
        self.instr1 = instr1
        self.instr2 = instr2
        self.bitwidth = bitwidth
        self.matsize = matsize
        self.use_nops = use_nops
        self.setup_rws = [f"RW {w}" for w in range(4, 4+setup_rw_ct)]
        self.base_distance = base_distance
        self.test_folder = test_folder
    
        self.l1 = None
        self.l2 = None
        self.hm2 = None
        self.ub2 = None
        self.acc2 = None
        self.flag1 = ""
        self.flag2 = ""

    def set_distance(self, new_distance):
        self.test_distance = new_distance

    def _mem_subfolder(self, mem_addr, mem_name):
        relative_addr = mem_addr - self.l2
        res = "/" + str(mem_name) + "2=" + str(mem_name) + "1"
        if relative_addr >= 0:
            res += "+"
        res += str(relative_addr)
        if mem_addr == 0:
            res += "^"
        return res

    def get_relative_filepath(self):
        fp = self.instr1 + "_" + self.instr2 + "/b" \
           + str(self.bitwidth) + "/m" + str(self.matsize)

        if self.l1 is not None or self.l2 is not None:
            fp += "/"
            if self.l1 is not None:
                fp += "l1=" + str(self.l1)
                if self.l2 is not None:
                    fp += "_"
            if self.l2 is not None:
                fp += "l2=" + str(self.l2)

        if self.hm2 is not None:
            fp += self._mem_subfolder(self.hm2, "hm")
        
        if self.ub2 is not None:
            fp += self._mem_subfolder(self.ub2, "ub")

        if self.acc2 is not None:
            fp += self._mem_subfolder(self.acc2, "acc")

        fp += "/w" + str(len(self.setup_rws))

        return fp


class ParamHandler:
    def __init__(self, func, instr1, instr2, bitwidth, matsize, use_nops, 
                 setup_rw_ct, base_distance, test_folder):
        
        self.func = func
        self.p = Params(instr1, instr2, bitwidth, matsize, use_nops, 
                        setup_rw_ct, base_distance, test_folder)

    def set_l1(self, l1):
        self.p.l1 = l1

    def set_l2(self, l2):
        self.p.l2 = l2

    def set_hm2(self, hm2):
        self.p.hm2 = hm2

    def set_ub2(self, ub2):
        self.p.ub2 = ub2

    def set_acc2(self, acc2):
        self.p.acc2 = acc2

    def set_flags1(self, flags):
        self.p.flag1 = "." + "".join(flags)

    def set_flags2(self, flags):
        self.p.flag2 = "." + "".join(flags)

    def get_driver_func(self):
        if self.p.use_nops:
            return self.n_mode_driver
        else:
            return self.h_mode_driver

    def get_dict_path_list(self):
        return self.p.get_relative_filepath().split("/")

    # run an N-mode squish test with a chosen set of Params.
    # this requires checking different distances in a binary search. 
    # binary search the distances in the range [1, START_DISTANCE) to find the 
    # minimum distance that works. 
    # return the lowest distance that was successful. 
    # if the final distance is reported as START_DISTANCE, it means that the 
    # test failed at all distances in the range. It could work at a distance 
    # d >= START_DISTANCE, or it could always fail. Either way, it's a signal to
    # investigate further and/or rerun with a higher START_DISTANCE.
    def n_mode_driver(self):
        # sys.stdout = open(os.devnull, 'w')
        left = 1
        right = self.p.base_distance
        while right - left > 0:
            mid = (left + right)//2
            self.p.set_distance(mid)
            result = self._param_passer()
            if result:
                right = mid
            else:
                left = mid+1
        return right

    # run an H-mode squish test with a chosen set of Params.
    def h_mode_driver(self):
        # sys.stdout = open(os.devnull, 'w')
        return self._param_passer()
    
    def _param_passer(self):
        setup, instrs = self.func(self.p)
        return squish_test(setup, instrs, self.p.test_distance, 
                           self.p.base_distance, self.p.bitwidth, 
                           self.p.matsize, self.p.use_nops, self.p.test_folder,
                           name=self.p.get_relative_filepath(),
                           reset=False, absoluteaddrs=True)
