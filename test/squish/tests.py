# Contains every parametrized squishtest
# One for every instr1_instr2 pair

from squishtest import squish_test
from test_utils import Params


### RHM TESTS ###


### RHM-RHM ###
# setup not needed
# instr1: RHM from HM addr `l2` to UB addr `l2` (this address lets instr2 fit 
#   completely before instr1 in the HM and UB address spaces)
# instr2: RHM from HM addr `hm2` to UB addr `ub2`
def rhm_rhm(p: Params):
    setup = p.setup_rws
    instrs = [f"RHM {p.l2} {p.l2} {p.l1}", f"RHM {p.hm2} {p.ub2} {p.l2}"]
    return setup, instrs

### RHM-WHM ###
# setup pre-fills the UB range accessed by instr2 (WHM) with values from unused
#   HM addresses
# instr1: RHM from HM addr `l2` to UB addr `l2` (this address lets instr2 fit
#   completely before instr1 in the HM and UB address spaces)
# instr2: WHM from UB addr `ub2` to HM addr `hm2`
def rhm_whm(p: Params):
    hm_max = max(p.l2+p.l1, p.hm2+p.l2)
    setup = p.setup_rws + [f"RHM {hm_max} {p.ub2} {p.l2}"]
    instrs = [f"RHM {p.l2} {p.l2} {p.l1}", f"WHM {p.hm2} {p.ub2} {p.l2}"]
    return setup, instrs

### RHM-RW ###
# setup not needed
# instr1: RHM from HM addr 0 to UB addr 0
# instr2: RW 0
def rhm_rw(p: Params):
    setup = p.setup_rws
    instrs = [f"RHM 0 0 {p.l1}", f"RW 0"]
    return setup, instrs

### RHM-MMC(.S) ###
# setup pre-fills the UB range accessed by instr2 (MMC/MMC.S) with values from 
#   unused HM addresses
# instr1: RHM from HM addr `l2` to UB addr `l2` (this address lets instr2 fit
#   completely before instr1 in the UB address space)
# instr2: MMC/MMC.S from UB addr `ub2` to ACC addr 0
def rhm_mmc(p: Params):
    setup = p.setup_rws + [f"RHM 0 {p.ub2} {p.l2}"]
    instrs = [f"RHM {p.l2} {p.l2} {p.l1}", f"MMC{p.flag2} 0 {p.ub2} {p.l2}"]
    return setup, instrs

### RHM-ACT ###
# setup pre-fills the accessed ACC range with values from unused HM and UB 
#   addresses (RHM from HM to UB, MMC from UB to ACC)
# instr1: RHM from HM addr `l2` to UB addr `l2` (this address lets instr2 fit 
#   completely before instr1 in the UB address space)
# instr2: ACT from ACC addr 0 to UB addr `ub2`
def rhm_act(p: Params):
    ub_max = max(p.l2+p.l1, p.ub2+p.l2)
    setup = [f"RHM {p.l2+p.l1} {ub_max} {p.l2}", "RW 2", 
             f"MMC.S 0 {ub_max} {p.l2}"] + p.setup_rws
    instrs = [f"RHM {p.l2} {p.l2} {p.l1}", f"ACT 0 {p.ub2} {p.l2}"]
    return setup, instrs

### RHM-HLT ###
# setup not needed
# instr1: RHM from HM addr 0 to UB addr 0
# instr2: Halt
def rhm_hlt(p: Params):
    setup = p.setup_rws
    instrs = [f"RHM 0 0 {p.l1}", f"HLT"]
    return setup, instrs


### WHM TESTS ###


### WHM-RHM ###
# setup pre-fills the UB range accessed by instr1 (WHM) with values from unused 
#   HM addresses
# instr1: WHM from UB addr `l2` to HM addr `l2` (this address lets instr2 fit
#   completely before instr1 in the HM and UB address spaces)
# instr2: RHM from HM addr `hm2` to UB addr `ub2`
def whm_rhm(p: Params):
    hm_max = max(p.l2+p.l1, p.hm2+p.l2)
    setup = p.setup_rws + [f"RHM {hm_max} {p.l2} {p.l1}"]
    instrs = [f"WHM {p.l2} {p.l2} {p.l1}", f"RHM {p.hm2} {p.ub2} {p.l2}"]
    return setup, instrs

### WHM-WHM ###
# setup pre-fills the UB ranges accessed by instr1 (WHM) and instr2 (WHM) with 
#   values from unused HM addresses
# instr1: WHM from UB addr `l2` to HM addr `l2` (this address lets instr2 fit
#   completely before instr1 in the HM and UB address spaces)
# instr2: WHM from UB addr `ub2` to HM addr `hm2`
def whm_whm(p: Params):
    hm_max = max(p.l2+p.l1, p.hm2+p.l2)
    setup = p.setup_rws + [f"RHM {hm_max} {p.l2} {p.l1}", 
                           f"RHM {hm_max+p.l1} {p.ub2} {p.l2}"]
    instrs = [f"WHM {p.l2} {p.l2} {p.l1}", f"WHM {p.hm2} {p.ub2} {p.l2}"]
    return setup, instrs

### WHM-RW ###
# setup pre-fills the UB range accessed by instr1 (WHM) with values from unused
#   HM addresses
# instr1: WHM from UB addr 0 to HM addr 0
# instr2: RW 0
def whm_rw(p: Params):
    setup = p.setup_rws + [f"RHM {p.l1} 0 {p.l1}"]
    instrs = [f"WHM 0 0 {p.l1}", "RW 0"]
    return setup, instrs

### WHM-MMC(.S) ###
# setup pre-fills the UB range accessed by instr1 (WHM) and instr2 (MMC/MMC.S)
#   with values from unused HM addresses
# instr1: WHM from UB addr `l2` to HM addr `l2` (this address lets instr2 fit
#   completely before instr1 in the UB address space)
# instr2: MMC/MMC.S from UB addr `ub2` to ACC addr 0
def whm_mmc(p: Params):
    hm_max = p.l2+p.l1
    setup = p.setup_rws + [f"RHM {hm_max} {p.l2} {p.l1}", 
                           f"RHM {hm_max+p.l1} {p.ub2} {p.l2}"]
    instrs = [f"WHM {p.l2} {p.l2} {p.l1}", f"MMC{p.flag2} 0 {p.ub2} {p.l2}"]
    return setup, instrs

### WHM-ACT ###
# setup pre-fills the UB range accessed by instr1 (WHM) with values from unused
#   HM addresses and the ACC range accessed by instr2 (ACT) with values from 
#   unused HM and UB addresses (RHM from HM to UB, MMC from UB to ACC)
# instr1: WHM from UB addr `l2` to HM addr `l2` (this address lets instr2 fit 
#   completely before instr1 in the UB address space)
# instr2: ACT from ACC addr 0 to UB addr `ub2`
def whm_act(p: Params):
    hm_max = p.l2+p.l1
    ub_max = max(p.l2+p.l1, p.ub2+p.l2)
    setup = [f"RHM {hm_max} {p.l2} {p.l1}", 
             f"RHM {hm_max+p.l1} {ub_max} {p.l2}", 
              "RW 2", f"MMC.S 0 {ub_max} {p.l2}"] + p.setup_rws
    instrs = [f"WHM {p.l2} {p.l2} {p.l1}", f"ACT 0 {p.ub2} {p.l2}"]
    return setup, instrs

### WHM-HLT ###
# setup pre-fills the UB range accessed by instr1 (WHM) with values from unused
#   HM addresses
# instr1: WHM from UB addr 0 to HM addr 0
# instr2: Halt
def whm_hlt(p: Params):
    setup = p.setup_rws + [f"RHM {p.l1} 0 {p.l1}"]
    instrs = [f"WHM 0 0 {p.l1}", "HLT"]
    return setup, instrs


### RW TESTS ###


### RW-RHM ###
# setup not needed
# instr1: RW 0
# instr2: RHM from HM addr 0 to UB addr 0
def rw_rhm(p: Params):
    setup = p.setup_rws
    instrs = ["RW 0", f"RHM 0 0 {p.l2}"]
    return setup, instrs

### RW-WHM ###
# setup pre-fills the UB range accessed by instr2 (WHM) with values from unused
#   HM addresses
# instr1: RW 0
# instr2: WHM from UB addr 0 to HM addr 0
def rw_whm(p: Params):
    setup = p.setup_rws + [f"RHM {p.l2} 0 {p.l2}"]
    instrs = ["RW 0", f"WHM 0 0 {p.l2}"]
    return setup, instrs

### RW-RW ###
# setup not needed
# instr1: RW 0
# instr2: RW 1
def rw_rw(p: Params):
    setup = p.setup_rws
    instrs = ["RW 0", "RW 1"]
    return setup, instrs

### RW-MMC(.S) ###
# setup pre-fills the UB ranges accessed by instr2 (MMC/MMC.S) with values from
#  unused HM addresses
# instr1: RW 0
# instr2: MMC/MMC.S from UB addr 0 to ACC addr 0
def rw_mmc(p: Params):
    setup = p.setup_rws + [f"RHM 0 0 {p.l2}"]
    instrs = ["RW 0", f"MMC{p.flag2} 0 0 {p.l2}"]
    return setup, instrs

### RW-ACT ###
# setup pre-fills the ACC range accessed by instr2 (ACT) with values from unused
#   HM and UB addresses (RHM from HM to UB, MMC from UB to ACC)
# instr1: RW 0
# instr2: ACT from ACC addr 0 to UB addr 0
def rw_act(p: Params):
    setup = [f"RHM 0 {p.l2} {p.l2}", "RW 2", f"MMC.S 0 {p.l2} {p.l2}"] \
          + p.setup_rws
    instrs = ["RW 0", f"ACT 0 0 {p.l2}"]
    return setup, instrs

### RW-HLT ###
# setup not needed
# instr1: RW 0
# instr2: Halt
def rw_hlt(p: Params):
    setup = p.setup_rws
    instrs = ["RW 0", "HLT"]
    return setup, instrs


### MMC TESTS ###


### MMC(.S)-RHM ###
# setup pre-fills the UB range accessed by instr1 (MMC/MMC.S) with values from
#   unused HM addresses
# instr1: MMC/MMC.S from UB addr `l2` to ACC addr 0 (this UB address lets instr2
#  fit completely before instr1 in the UB address space)
# instr2: RHM from HM addr 0 to UB addr `ub2` 
def mmc_rhm(p: Params):
    setup = p.setup_rws + [f"RHM {p.l2} {p.l2} {p.l1}"]
    instrs = [f"MMC{p.flag1} 0 {p.l2} {p.l1}", f"RHM 0 {p.ub2} {p.l2}"]
    return setup, instrs

### MMC(.S)-WHM ###
# setup pre-fills the UB range accessed by instr1 (MMC/MMC.S) and instr2 (WHM)
#   with values from unused HM addresses
# instr1: MMC/MMC.S from UB addr `l2` to ACC addr 0 (this UB address lets instr2
#   fit completely before instr1 in the UB address space)
# instr2: WHM from UB addr `ub2` to HM addr 0
def mmc_whm(p: Params):
    setup = p.setup_rws + [f"RHM {p.l2} {p.l2} {p.l1}", 
                           f"RHM {p.l2+p.l1} {p.ub2} {p.l2}"]
    instrs = [f"MMC{p.flag1} 0 {p.l2} {p.l1}", f"WHM 0 {p.ub2} {p.l2}"]
    return setup, instrs

### MMC(.S)-RW ###
# setup pre-fills the UB range accessed by instr1 (MMC/MMC.S) with values from
#   unused HM addresses
# instr1: MMC/MMC.S from UB addr 0 to ACC addr 0
# instr2: RW 0
def mmc_rw(p: Params):
    setup = p.setup_rws + [f"RHM 0 0 {p.l1}"]
    instrs = [f"MMC{p.flag1} 0 0 {p.l1}", "RW 0"]
    return setup, instrs

### MMC(.S)-MMC(.S) ###
# setup pre-fills the UB ranges accessed by instr1 (MMC/MMC.S) and instr2 
#   (MMC/MMC.S) with values from unused HM addresses
# instr1: MMC/MMC.S from UB addr `l2` to ACC addr `l2` (these UB and ACC 
#   addresses let instr2 fit completely before instr1 in the UB and ACC address
#   spaces)
# instr2: MM/MMC.S from UB addr `ub2` to ACC addr `acc2`
def mmc_mmc(p: Params):
    setup = p.setup_rws + [f"RHM 0 {p.l2} {p.l1}", 
                           f"RHM {p.l1} {p.ub2} {p.l2}"]
    instrs = [f"MMC{p.flag1} {p.l2} {p.l2} {p.l1}", 
              f"MMC{p.flag2} {p.acc2} {p.ub2} {p.l2}"]
    return setup, instrs

### MMC(.S)-ACT ###
# setup pre-fills the UB range accessed by instr1 (MMC/MMC.S) with values from
#   unused HM addresses and the ACC range accessed by instr2 (ACT) with values 
#   from unused HM and UB addresses (RHM from HM to UB, MMC from UB to ACC)
# instr1: MMC/MMC.S from UB addr `l2` to ACC addr `l2` (this address lets instr2
#   fit completely before instr1 in the UB and ACC address spaces)
# instr2: ACT from ACC addr `acc2` to UB addr `ub2`
def mmc_act(p: Params):
    ub_max = max(p.l2+p.l1, p.ub2+p.l2)
    setup = p.setup_rws + [f"RHM 0 {p.l2} {p.l1}", 
                           f"RHM {p.l1} {ub_max} {p.l2}", 
                           f"MMC {p.acc2} {ub_max} {p.l2}"]
    instrs = [f"MMC{p.flag1} {p.l2} {p.l2} {p.l1}", 
              f"ACT {p.acc2} {p.ub2} {p.l2}"]
    return setup, instrs

### MMC(.S)-HLT TESTS ###
# setup pre-fills the UB range accessed by instr1 (MMC/MMC.S) with values from
#   unused HM addresses
# instr1: MMC/MMC.S from UB addr 0 to ACC addr 0
# instr2: Halt
def mmc_hlt(p: Params):
    setup = p.setup_rws + [f"RHM 0 0 {p.l1}"]
    instrs = [f"MMC{p.flag1} 0 0 {p.l1}", "HLT"]
    return setup, instrs


### ACT TESTS ###


### ACT-RHM ###
# setup pre-fills the ACC range accessed by instr1 (ACT) with values from unused
#   HM and UB addresses (RHM from HM to UB, MMC.S from UB to ACC)
# instr1: ACT from ACC addr 0 to ub addr `l2` (this address lets instr2 fit 
#   completely before instr1 in the UB address space)
# instr2: RHM from HM addr 0 to ub addr `ub2`
def act_rhm(p: Params):
    ub_max = max(p.l2+p.l1, p.ub2+p.l2)
    setup = [f"RHM {p.l2} {ub_max} {p.l1}", "RW 2", 
             f"MMC.S 0 {ub_max} {p.l1}"] + p.setup_rws
    instrs = [f"ACT 0 {p.l2} {p.l1}", f"RHM 0 {p.ub2} {p.l2}"]
    return setup, instrs

### ACT-WHM ###
# setup pre-fills the ACC range accessed by instr1 (ACT) with values from unused
#   HM and UB addresses (RHM from HM to UB, MMC.S from UB to ACC) and the UB 
#   range accessed by instr2 (WHM) with values from unused HM addresses
# instr1: ACT from ACC addr 0 to UB addr `l2` (this address lets instr2 fit 
#   completely before instr1 in the UB address space)
# instr2: WHM from UB addr `ub2` to HM addr 0
def act_whm(p: Params):
    ub_max = max(p.l2+p.l1, p.ub2+p.l2)
    setup = [f"RHM {p.l2} {ub_max} {p.l1}", "RW 2", f"MMC.S 0 {ub_max} {p.l1}", 
             f"RHM {p.l2+p.l1} {p.ub2} {p.l2}"] + p.setup_rws
    instrs = [f"ACT 0 {p.l2} {p.l1}", f"WHM 0 {p.ub2} {p.l2}"]
    return setup, instrs

### ACT-RW ###
# setup pre-fills the ACC range accessed by instr1 (ACT) with values from unused
#   HM and UB addresses (RHM from HM to UB, MMC.S from UB to ACC)
# instr1: ACT from ACC addr 0 to UB addr 0
# instr2: RW 0
def act_rw(p: Params):
    setup = [f"RHM 0 {p.l1} {p.l1}", "RW 2", f"MMC.S 0 {p.l1} {p.l1}"] \
          + p.setup_rws
    instrs = [f"ACT 0 0 {p.l1}", "RW 0"]
    return setup, instrs

### ACT-MMC(.S) ###
# setup pre-fills the ACC range accessed by instr1 (ACT) with values from unused
#   HM and UB addresses (RHM from HM to UB, MMC from UB to ACC) and the UB range
#   accessed by instr2 (MMC/MMC.S) with values from unused HM addresses
# instr1: ACT from ACC addr `l2` to UB addr `l2` (these addresses let instr2 fit 
#   completely before instr1 in the UB and ACC address spaces)
# instr2: MMC from UB addr `ub2` to ACC addr `acc2`
def act_mmc(p: Params):
    ub_max = max(p.l2+p.l1, p.ub2+p.l2)
    setup = p.setup_rws + [f"RHM 0 {ub_max} {p.l1}", 
                           f"MMC {p.l2} {ub_max} {p.l1}", 
                           f"RHM {p.l1} {p.ub2} {p.l2}"]
    instrs = [f"ACT {p.l2} {p.l2} {p.l1}", 
              f"MMC{p.flag2} {p.acc2} {p.ub2} {p.l2}"]
    return setup, instrs

### ACT-ACT ###
# setup pre-fills the ACC ranges accessed by instr1 (ACT) and instr2 (ACT) with
#   values from unused HM and UB addressed (RHM from HM to UB, MMC.S from UB to
#   ACC)
# instr1: ACT from ACC addr `l2` to UB addr `l2` (these addresses let instr2 fit 
#   completely before instr1 in the UB and ACC address spaces)
# instr2: ACT from ACC addr `acc2` to UB addr `ub2`
def act_act(p: Params):
    ub_max = max(p.l2+p.l1, p.ub2+p.l2)
    setup = [f"RHM 0 {ub_max} {p.l1}", "RW 2", f"MMC.S {p.l2} {ub_max} {p.l1}", 
             f"RHM {p.l1} {ub_max+p.l1} {p.l2}", "RW 3", 
             f"MMC.S {p.acc2} {ub_max+p.l1} {p.l2}"] + p.setup_rws
    instrs = [f"ACT {p.l2} {p.l2} {p.l1}", f"ACT {p.acc2} {p.ub2} {p.l2}"]
    return setup, instrs

### ACT-HLT ###
# setup pre-fills the ACC range accessed by instr1 (ACT) with values from unused
#   HM and UB addresses (RHM from HM to UB, MMC.S from UB to ACC)
# instr1: ACT from ACC addr 0 to UB addr 0
# instr2: Halt
def act_hlt(p: Params):
    setup = [f"RHM 0 {p.l1} {p.l1}", "RW 2", f"MMC.S 0 {p.l1} {p.l1}"] \
          + p.setup_rws
    instrs = [f"ACT 0 0 {p.l1}", "HLT"]
    return setup, instrs


### CUSTOM TESTS ###


# test the behavior of the MMC switch instruction. the expected behavior is that
# a loaded weight will enter the back of the queue. An MMC with or without the
# .S flag will use the weight at the front of the queue. If the .S flag is not
# used, then the instruction will use the front weight and not switch it. If the
# .S is used, then the instruction will use the front weight and afterwards, 
# discard the front instruction to let the next one come to the front.
# this test loads HM0, HM1, and HM2 to UB0, UB1, and UB2, respectively.
# it then loads RW0 and RW1 to the weight queue.
# it then does the following multiplication operations:
#     UB0 * RW0 -> ACC0 (no .S)
#     UB1 * RW0 -> ACC1 (.S)
#     UB2 * RW1 -> ACC2 (.S but it doesn't matter)
# it then writes ACC0 to UB3, ACC1 to UB4, and ACC2 to UB5.
# it then writes UB3 to HM3, UB4 to HM4, and UB5 to HM5.
# the expected results are that HM3 = HM0 * RW0, HM4 = HM1 * RW0, and 
# HM5 = HM2 * RW1.
def test_mmc_switch_behavior(p: Params):
    setup = p.setup_rws + ["RHM 0 0 1", "RHM 1 1 1", "RHM 2 2 1", "MMC 0 0 1", 
                           "MMC.S 1 1 1", "MMC.S 2 2 1", "ACT 0 3 1",
                           "ACT 1 4 1", "ACT 2 5 1", "WHM 3 3 1", "WHM 4 4 1", 
                           "WHM 5 5 1"],
    instrs = ["NOP", "NOP"]
    return setup, instrs
