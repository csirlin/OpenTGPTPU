This set of tests squishes instructions next to each other closer and closer until something breaks.
This gives an empirical idea of how close different instructions can get to one another (or even if they can overlap!)

Want to test with different matrix sizes and bitwidths! \
So the distance, bitwidth, and matsize parameters will vary with testing

### RHM/RHM: 
from HM0 to UB0 and from HM1 to UB1 (no overlap in HM or UB) \
```python test/squish/squishtest.py "RHM 0 0 1" "RHM 1 1 1" -n "rhm_rhm_no_overlap" -s "RHM 2 0 1" -s "RHM 3 1 1" -c "WHM 2 0 1" -c "WHM 3 1 1"```

from HM0 to UB0 and from HM1 to UB0 (same destination in UB) \
```python test/squish/squishtest.py "RHM 0 0 1" "RHM 1 0 1" -n "rhm_rhm_same_ub" -s "RHM 2 0 1" -s "RHM 3 1 1" -c "WHM 2 0 1" -c "WHM 3 1 1"```

from HM0 to UB0 and from HM0 to UB1 (same origin in HM) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and from HM0 to UB0 (same origin in HM and destination in UB) \
```python test/squish/squishtest.py ```


### RHM/WHM:
from HM0 to UB0 and from UB1 to HM1 (no overlap in HM or UB) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and from UB0 to HM1 (same UB) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and from UB1 to HM0 (same HM) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and from UB0 to HM0 (same UB and HM) \
```python test/squish/squishtest.py ```


### RHM/RW:
from HM0 to UB0 and reading from RW0 \
```python test/squish/squishtest.py ```


### RHM/MMC:
from HM0 to UB0 and multiplying UB0 with ACC0, no .S (same UB) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and multiplying UB1 with ACC0, no .S (different UBs) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and multiplying UB0 with ACC0, w/ .S (same UB) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and multiplying UB1 with ACC0, w/ .S (different UBs) \
```python test/squish/squishtest.py ```


### RHM/ACT:
from HM0 to UB0 and accumulate from ACC0 to UB0 (same UB) \
```python test/squish/squishtest.py ```

from HM0 to UB0 and accumulate from ACC0 to UB1 (different UBs) \
```python test/squish/squishtest.py ```


### WHM/RHM:
from UB0 to HM0 and from HM1 to UB1 (no overlap in HM or UB) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and from HM1 to UB0 (same UB) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and from HM0 to UB1 (same HM) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and from HM0 to UB0 (same UB and HM) \
```python test/squish/squishtest.py ```


### WHM/WHM:
from UB0 to HM0 and from UB1 to HM1 (no overlap in HM or UB) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and from UB1 to HM0 (same destination in HM) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and from UB0 to HM1 (same origin in UB) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and from UB0 to HM0 (same origin in UB and destination in HM) \
```python test/squish/squishtest.py ```


### WHM/RW:
from UB0 to HM0 and reading from RW0 \
```python test/squish/squishtest.py ```


### WHM/MMC:
from UB0 to HM0 and multiplying UB0 into ACC0, no .S (same UB) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and multiplying UB1 into ACC0, no .S (different UBs) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and multiplying UB0 into ACC0, w/ .S (same UB) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and multiplying UB1 into ACC0, w/ .S (different UBs) \
```python test/squish/squishtest.py ```


### WHM/ACT:
from UB0 to HM0 and accumulate from ACC0 to UB0 (same UB) \
```python test/squish/squishtest.py ```

from UB0 to HM0 and accumulate from ACC0 to UB1 (different UBs) \
```python test/squish/squishtest.py ```


### RW/RHM:
reading from RW0 and moving from HM0 to UB0 \
```python test/squish/squishtest.py ```


### RW/WHM:
reading from RW0 and moving from UB0 to HM0 \
```python test/squish/squishtest.py ```


### RW/RW:
reading from RW0 and RW0, buffer starts empty (same weights) \
```python test/squish/squishtest.py ```

reading from RW0 and RW1, buffer starts empty (different weights) \
```python test/squish/squishtest.py ```

reading from RW0 and RW0, buffer starts with one space (same weights) \
```python test/squish/squishtest.py ```

reading from RW0 and RW1, buffer starts with one space (different weights) \
```python test/squish/squishtest.py ```

reading from RW0 and RW0, buffer starts full (same weights) \
```python test/squish/squishtest.py ```

reading from RW0 and RW1, buffer starts full (different weights) \
```python test/squish/squishtest.py ```


### RW/MMC:
reading from RW0, buffer starts empty, multiplying UB0 into ACC0, no .S \
```python test/squish/squishtest.py ```

reading from RW0, buffer starts empty, multiplying UB0 into ACC0, w/ .S \
```python test/squish/squishtest.py ```

reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, no .S \
```python test/squish/squishtest.py ```

reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, w/ .S \
```python test/squish/squishtest.py ```

reading from RW0, buffer starts full, multiplying UB0 into ACC0, no .S \
```python test/squish/squishtest.py ```

reading from RW0, buffer starts full, multiplying UB0 into ACC0, w/ .S \
```python test/squish/squishtest.py ```


### RW/ACT:
reading from RW0 and accumulate from ACC0 to UB0 \
```python test/squish/squishtest.py ```


### MMC/RHM:
multiplying UB0 into ACC0, no .S, moving from HM0 to UB0 (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB0 (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, no .S, moving from HM0 to UB1 (different UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB1 (different UB) \
```python test/squish/squishtest.py ```


### MMC/WHM:
multiplying UB0 into ACC0, no .S, moving from UB0 to HM0 (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, w/ .S, moving from UB0 to HM0 (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, no .S, moving from UB1 to HM0 (different UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, w/ .S, moving from UB1 to HM0 (different UB) \
```python test/squish/squishtest.py ```


### MMC/RW:
multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts empty \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts empty \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts with one space \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts with one space \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts full \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts full \
```python test/squish/squishtest.py ```


### MMC/MMC:
multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 no .S (different UB and ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 no .S (different UB and ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC) \
```python test/squish/squishtest.py ```


multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 no .S (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 w/ .S (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 no .S (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 w/ .S (same UB) \
```python test/squish/squishtest.py ```


multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 no .S (same ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 w/ .S (same ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 no .S (same ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 w/ .S (same ACC) \
```python test/squish/squishtest.py ```


multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 no .S (same ACC and UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 no .S (same ACC and UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB) \
```python test/squish/squishtest.py ```


### MMC/ACT:
multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB1 (different UB and ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB1 (different UB and ACC) \
```python test/squish/squishtest.py ```


multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB0 (same UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB0 (same UB) \
```python test/squish/squishtest.py ```


multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB1 (same ACC) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB1 (same ACC) \
```python test/squish/squishtest.py ```


multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB0 (same ACC and UB) \
```python test/squish/squishtest.py ```

multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB0 (same ACC and UB) \
```python test/squish/squishtest.py ```


### ACT/RHM:
accumulate from ACC0 to UB0, move from HM0 to UB0 (same UB) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, move from HM0 to UB1 (different UB) \
```python test/squish/squishtest.py ```


### ACT/WHM:
accumulate from ACC0 to UB0, move from UB0 to HM0 (same UB) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, move from UB1 to HM0 (different UB) \
```python test/squish/squishtest.py ```


### ACT/RW:
accumulate from ACC0 to UB0, read from RW0 \
```python test/squish/squishtest.py ```


### ACT/MMC:
accumulate from ACC0 to UB0, multiplying UB0 into ACC0 no .S (different UB) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, multiplying UB0 into ACC0 w/ .S (different UB) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, multiplying UB1 into ACC0 no .S (same UB) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, multiplying UB1 into ACC0 w/ .S (same UB) \
```python test/squish/squishtest.py ```


### ACT/ACT:
accumulate from ACC0 to UB0, accumulate from ACC1 to UB1 (different UB and ACC) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, accumulate from ACC1 to UB0 (same UB) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, accumulate from ACC0 to UB1 (same ACC) \
```python test/squish/squishtest.py ```

accumulate from ACC0 to UB0, accumulate from ACC0 to UB0 (same UB and ACC) \
```python test/squish/squishtest.py ```

