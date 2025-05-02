This set of tests squishes instructions next to each other closer and closer until something breaks.
This gives an empirical idea of how close different instructions can get to one another (or even if they can overlap!)

Want to test with different matrix sizes and bitwidths! \
So the distance, bitwidth, and matsize parameters will vary with testing

### RHM/RHM: 
from HM0 to UB0 and from HM1 to UB1 (no overlap in HM or UB) \
from HM0 to UB0 and from HM1 to UB0 (same destination in UB) \
from HM0 to UB0 and from HM0 to UB1 (same origin in HM) \
from HM0 to UB0 and from HM0 to UB0 (same origin in HM and destination in UB)

### RHM/WHM:
from HM0 to UB0 and from UB1 to HM1 (no overlap in HM or UB) \
from HM0 to UB0 and from UB0 to HM1 (same UB) \
from HM0 to UB0 and from UB1 to HM0 (same HM) \
from HM0 to UB0 and from UB0 to HM0 (same UB and HM)

### RHM/RW:
from HM0 to UB0 and reading from RW0

### RHM/MMC:
from HM0 to UB0 and multiplying UB0 with ACC0, no .S (same UB) \
from HM0 to UB0 and multiplying UB1 with ACC0, no .S (different UBs) \
from HM0 to UB0 and multiplying UB0 with ACC0, w/ .S (same UB) \
from HM0 to UB0 and multiplying UB1 with ACC0, w/ .S (different UBs)

### RHM/ACT:
from HM0 to UB0 and accumulate from ACC0 to UB0 (same UB) \
from HM0 to UB0 and accumulate from ACC0 to UB1 (different UBs)

### RHM/HLT:
from HM0 to UB0 and halt

### WHM/RHM:
from UB0 to HM0 and from HM1 to UB1 (no overlap in HM or UB) \
from UB0 to HM0 and from HM1 to UB0 (same UB) \
from UB0 to HM0 and from HM0 to UB1 (same HM) \
from UB0 to HM0 and from HM0 to UB0 (same UB and HM)

### WHM/WHM:
from UB0 to HM0 and from UB1 to HM1 (no overlap in HM or UB) \
from UB0 to HM0 and from UB1 to HM0 (same destination in HM) \
from UB0 to HM0 and from UB0 to HM1 (same origin in UB) \
from UB0 to HM0 and from UB0 to HM0 (same origin in UB and destination in HM)

### WHM/RW:
from UB0 to HM0 and reading from RW0

### WHM/MMC:
from UB0 to HM0 and multiplying UB0 into ACC0, no .S (same UB) \
from UB0 to HM0 and multiplying UB1 into ACC0, no .S (different UBs) \
from UB0 to HM0 and multiplying UB0 into ACC0, w/ .S (same UB) \
from UB0 to HM0 and multiplying UB1 into ACC0, w/ .S (different UBs)

### WHM/ACT:
from UB0 to HM0 and accumulate from ACC0 to UB0 (same UB) \
from UB0 to HM0 and accumulate from ACC0 to UB1 (different UBs)

### WHM/HLT:
from UB0 to HM and halt

### RW/RHM:
reading from RW0 and moving from HM0 to UB0

### RW/WHM:
reading from RW0 and moving from UB0 to HM0

### RW/RW:
reading from RW0 and RW0, buffer starts empty (same weights) \
reading from RW0 and RW1, buffer starts empty (different weights) \
reading from RW0 and RW0, buffer starts with one space (same weights) \
reading from RW0 and RW1, buffer starts with one space (different weights) \
reading from RW0 and RW0, buffer starts full (same weights) \
reading from RW0 and RW1, buffer starts full (different weights)

### RW/MMC:
reading from RW0, buffer starts empty, multiplying UB0 into ACC0, no .S \
reading from RW0, buffer starts empty, multiplying UB0 into ACC0, w/ .S \
reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, no .S \
reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, w/ .S \
reading from RW0, buffer starts full, multiplying UB0 into ACC0, no .S \
reading from RW0, buffer starts full, multiplying UB0 into ACC0, w/ .S

### RW/ACT:
reading from RW0 and accumulate from ACC0 to UB0

### RW/HLT:
reading from RW0, buffer starts empty, halting \
reading from RW0, buffer starts with one space, halting \
reading from RW0, buffer starts full, halting

### MMC/RHM:
multiplying UB0 into ACC0, no .S, moving from HM0 to UB0 (same UB) \
multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB0 (same UB) \
multiplying UB0 into ACC0, no .S, moving from HM0 to UB1 (different UB) \
multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB1 (different UB)

### MMC/WHM:
multiplying UB0 into ACC0, no .S, moving from UB0 to HM0 (same UB) \
multiplying UB0 into ACC0, w/ .S, moving from UB0 to HM0 (same UB) \
multiplying UB0 into ACC0, no .S, moving from UB1 to HM0 (different UB) \
multiplying UB0 into ACC0, w/ .S, moving from UB1 to HM0 (different UB)

### MMC/RW:
multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts empty \
multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts empty \
multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts with one space \
multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts with one space \
multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts full \
multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts full

### MMC/MMC:
multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 no .S (different UB and ACC) \
multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC) \
multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 no .S (different UB and ACC) \
multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC)

multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 no .S (same UB) \
multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 w/ .S (same UB) \
multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 no .S (same UB) \
multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 w/ .S (same UB)

multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 no .S (same ACC) \
multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 w/ .S (same ACC) \
multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 no .S (same ACC) \
multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 w/ .S (same ACC)

multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 no .S (same ACC and UB) \
multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB) \
multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 no .S (same ACC and UB) \
multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB)

### MMC/ACT:
multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB1 (different UB and ACC) \
multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB1 (different UB and ACC)

multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB0 (same UB) \
multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB0 (same UB)

multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB1 (same ACC) \
multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB1 (same ACC)

multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB0 (same ACC and UB) \
multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB0 (same ACC and UB)

### MMC/HLT:
multiplying UB0 into ACC0 no .S, halting, buffer starts empty \
multiplying UB0 into ACC0 w/ .S, halting, buffer starts empty \
multiplying UB0 into ACC0 no .S, halting, buffer starts with one space \
multiplying UB0 into ACC0 w/ .S, halting, buffer starts with one space \
multiplying UB0 into ACC0 no .S, halting, buffer starts full \
multiplying UB0 into ACC0 w/ .S, halting, buffer starts full

### ACT/RHM:
accumulate from ACC0 to UB0, move from HM0 to UB0 (same UB) \
accumulate from ACC0 to UB0, move from HM0 to UB1 (different UB)

### ACT/WHM:
accumulate from ACC0 to UB0, move from UB0 to HM0 (same UB) \
accumulate from ACC0 to UB0, move from UB1 to HM0 (different UB)

### ACT/RW:
accumulate from ACC0 to UB0, read from RW0

### ACT/MMC:
accumalate from ACC0 to UB0, multiplying UB1 into ACC1 no .S (different ACC and UB) \
accumulate from ACC0 to UB0, multiplying UB1 into ACC1 w/ .S (different ACC and UB) \
accumulate from ACC0 to UB0, multiplying UB0 into ACC1 no .S (same UB) \
accumulate from ACC0 to UB0, multiplying UB0 into ACC1 w/ .S (same UB) \
accumulate from ACC0 to UB0, multiplying UB1 into ACC0 no .S (same ACC) \
accumulate from ACC0 to UB0, multiplying UB1 into ACC0 w/ .S (same ACC) \
accumulate from ACC0 to UB0, multiplying UB0 into ACC0 no .S (same ACC and UB) \
accumulate from ACC0 to UB0, multiplying UB0 into ACC0 w/ .S (same ACC and UB)

### ACT/ACT:
accumulate from ACC0 to UB0, accumulate from ACC1 to UB1 (different UB and ACC) \
accumulate from ACC0 to UB0, accumulate from ACC1 to UB0 (same UB) \
accumulate from ACC0 to UB0, accumulate from ACC0 to UB1 (same ACC) \
accumulate from ACC0 to UB0, accumulate from ACC0 to UB0 (same UB and ACC)

### ACT/HLT:
accumulate from ACC0 to UB0, halt
