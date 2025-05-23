from functools import reduce
from pyrtl import *
from pyrtl import rtllib, corecircuits
from pyrtl.rtllib import multipliers

#set_debug_mode()
globali = 0  # To give unique numbers to each MAC
def MAC(data_width, matrix_size, data_in, acc_in, switchw, weight_in, weight_we,
         weight_tag, BITWIDTH, i, j):
    '''Multiply-Accumulate unit with programmable weight.
    Inputs
    data_in: The 8-bit activation value to multiply by weight.
    acc_in: BITWIDTH-bit value to accumulate with product.
    switchw: Control signal; when 1, switch to using the other weight buffer.
    weight_in: 8-bit value to write to the secondary weight buffer.
    weight_we: When high, weights are being written; if tag matches, store weights.
               Otherwise, pass them through with incremented tag.
    weight_tag: If equal to 255, weight is for this row; store it.

    Outputs
    out: Result of the multiply accumulate; moves one cell down to become acc_in.
    data_reg: data_in, stored in a pipeline register for cell to the right.
    switch_reg: switchw, stored in a pipeline register for cell to the right.
    weight_reg: weight_in, stored in a pipeline register for cell below.
    weight_we_reg: weight_we, stored in a pipeline register for cell below.
    weight_tag_reg: weight_tag, incremented and stored in a pipeline register for cell below
    '''
    # print(f"MAC({data_width}, {matrix_size}, {len(data_in)}, {len(acc_in)}, \
    #       {len(switchw)}, {len(weight_in)}, {len(weight_we)}, {len(weight_tag)} \
    #        , {i}, {j})")
    global globali
    # Check lengths of inupts
    if len(weight_in) != len(data_in) != data_width:
        raise Exception("Expected 8-bit value in MAC.")
    if len(switchw) != len(weight_we) != 1:
        raise Exception("Expected 1-bit control signal in MAC.")

    # Should never switch weight buffers while they're changing
    #rtl_assert(~(weight_we & switchw), Exception("Cannot switch weight values when they're being loaded!"))

    # Use two buffers to store weight and next weight to use.
    wbuf1 = Register(len(weight_in), f"mac_wbuf1_{i}_{j}")
    wbuf2 = Register(len(weight_in), f"mac_wbuf2_{i}_{j}")

    switchw_wv = WireVector(1, f"mac_switch_wv_{i}_{j}")
    switchw_wv <<= switchw

    # Track which buffer is current and which is secondary.
    current_buffer_reg = Register(1, f"mac_current_buffer_reg_{i}_{j}")
    with conditional_assignment:
        with switchw:
            current_buffer_reg.next |= ~current_buffer_reg
    current_buffer = WireVector(1, f"mac_current_buffer_{i}_{j}")
    current_buffer <<= current_buffer_reg ^ switchw  # reflects change in same cycle switchw goes high

    # When told, store a new weight value in the secondary buffer
    with conditional_assignment:
        with weight_we & (weight_tag == Const(matrix_size-1)):
            with current_buffer == 0:  # If 0, wbuf1 is current; if 1, wbuf2 is current
                wbuf2.next |= weight_in
            with otherwise:
                wbuf1.next |= weight_in

    # Do the actual MAC operation
    weight = WireVector(len(weight_in), f"mac_weight_{i}_{j}") 
    weight <<= select(current_buffer, wbuf2, wbuf1)
    #probe(weight, "weight" + str(globali))
    globali += 1
    #inlen = max(len(weight), len(data_in))
    #product = weight.sign_extended(inlen*2) * data_in.sign_extended(inlen*2)
    #product = product[:inlen*2]
    product = WireVector(len(weight) + len(data_in), f"mac_product_{i}_{j}")
    
    # just use the passed in weight. it should be using whatever is at buf4 at the time.
    product <<= corecircuits.signed_mult(weight_in, data_in)[:data_width] 

    #plen = len(weight) + len(data_in)
    #product = weight.sign_extended(plen) * data_in.sign_extended(plen)
    #product = product[:plen]
    l = max(len(product), len(acc_in)) + 1
    out = (product.sign_extended(l) + acc_in.sign_extended(l))[:-1]

    #product = rtllib.multipliers.signed_tree_multiplier(weight, data_in)
    #l = max(len(product), len(acc_in))
    #out = product.sign_extended(l) + acc_in.sign_extended(l)

    if len(out) > BITWIDTH:
        out = out[:BITWIDTH]
                
    # For values that need to be forward to the right/bottom, store in pipeline registers
    data_reg = Register(len(data_in), f"mac_data_reg_{i}_{j}")  # pipeline register, holds data value for cell to the right
    data_reg.next <<= data_in
    switch_reg = Register(1, f"mac_switch_reg_{i}_{j}")  # pipeline register, holds switch control signal for cell to the right
    switch_reg.next <<= switchw
    acc_reg = Register(len(out), f"mac_acc_reg_{i}_{j}")  # output value for MAC below
    acc_reg.next <<= out
    weight_reg = Register(len(weight_in), f"mac_weight_reg_{i}_{j}")  # pipeline register, holds weight input for cell below
    weight_reg.next <<= weight_in
    weight_we_reg = Register(1, f"mac_weight_we_reg_{i}_{j}")  # pipeline register, holds weight write enable signal for cell below
    weight_we_reg.next <<= weight_we
    weight_tag_reg = Register(len(weight_tag), f"mac_weight_tag_reg_{i}_{j}")  # pipeline register, holds weight tag for cell below
    weight_tag_reg.next <<= (weight_tag + 1)[:len(weight_tag)]  # increment tag as it passes down rows

    return acc_reg, data_reg, switch_reg, weight_reg, weight_we_reg, weight_tag_reg

    
def MMArray(data_width, matrix_size, data_in, new_weights, weights_in, 
            weights_we, BITWIDTH):
    '''
    data_in: 256-array of 8-bit activation values from systolic_setup buffer
    new_weights: 256-array of 1-bit control values indicating that new weight should be used
    weights_in: output of weight FIFO (8 x matsize x matsize bit wire)
    weights_we: 1-bit signal to begin writing new weights into the matrix
    '''



    # For signals going to the right, store in a var; for signals going down, keep a list
    # For signals going down, keep a copy of inputs to top row to connect to later
    weights_in_top = [ WireVector(data_width, f"mma_weights_in_top_{i}") for i in range(matrix_size) ]  # input weights to top row
    weights_in_last = [x for x in weights_in_top]
    weights_enable_top = [ WireVector(1, f"mma_weights_enable_top_{i}") for i in range(matrix_size) ]  # weight we to top row
    weights_enable = [x for x in weights_enable_top]
    weights_tag_top = [ WireVector(data_width, f"mma_weights_tag_top_{i}") for i in range(matrix_size) ]  # weight row tag to top row
    weights_tag = [x for x in weights_tag_top]
    data_out = [Const(0) for i in range(matrix_size)]  # will hold output from final row

    
    # Handle weight reprogramming
    programming = Register(1, "mma_programming")  # when 1, we're in the process of loading new weights
    size = 1
    while pow(2, size) < matrix_size:
        size = size + 1
    progstep = Register(size, "mma_progstep")  # 256 steps to program new weights (also serves as tag input)
    with conditional_assignment:
        with weights_we & (~programming):
            programming.next |= 1
        with programming & (progstep == matrix_size-1):
            programming.next |= 0
        with otherwise:
            pass
        with programming:  # while programming, increment state each cycle
            progstep.next |= progstep + 1
        with otherwise:
            progstep.next |= Const(0)

    # Divide FIFO output into rows (each row datawidth x matrixsize bits)
    rowsize = data_width * matrix_size
    # print(f"Matrix_size: {matrix_size}, rowsize: {rowsize}, len(weights_in): {len(weights_in)}")
    weight_arr = [ weights_in[i*rowsize : i*rowsize + rowsize] for i in range(matrix_size) ] # weight_arr[i] is row i (bottom row is 0). # cells written from left to right.

    for i in range(len(weight_arr)):
        weight_arr_i = WireVector(len(weight_arr[i]), f"mma_weight_arr_{i}")
        weight_arr_i <<= weight_arr[i]

    # cells[i][j] is the value at row i, column j of fifo_buf4, with top left being (row 0, col 0)
    # way more straightforward than the original system for what we need
    cells = [ [ weight_arr[i][j*data_width:j*data_width+data_width] for j in reversed(range(matrix_size)) ] for i in reversed(range(matrix_size)) ]
    for i in range(len(cells)):
        for j in range(len(cells[i])):
            cells[i][j].name = f"mma_cells_{i}_{j}"

    # Mux the wire for this row
    current_weights_wire = mux(progstep, *weight_arr)
    # Split the wire into an array of 8-bit values
    current_weights = [ current_weights_wire[i*data_width:i*data_width+data_width] for i in reversed(range(matrix_size)) ]

    for i in range(len(current_weights)):
        current_weights_i = WireVector(len(current_weights[i]), f"mma_current_weights_{i}")
        current_weights_i <<= current_weights[i]

    # Connect top row to input and control signals
    for i, win in enumerate(weights_in_top):
        # From the current 256-array, select the byte for this column
        win <<= current_weights[i]
    for we in weights_enable_top:
        # Whole row gets same signal: high when programming new weights
        we <<= programming
    for wt in weights_tag_top:
        # Tag is same for whole row; use state index (runs from 0 to 255)
        wt <<= progstep

    # Build array of MACs
    for i in range(matrix_size):  # for each row
        din = data_in[i]
        switchin = new_weights[i]
        #probe(switchin, "switch" + str(i))
        for j in range(matrix_size):  # for each column
            # bitwidth stored in a wv
            data_width_in = WireVector(32, f"mma_in_data_width_{i}_{j}")
            data_width_in <<= data_width
            # matsize stored in a wv
            matrix_size_in = WireVector(32, f"mma_in_matrix_size_{i}_{j}")
            matrix_size_in <<= matrix_size
            din_in = WireVector(len(din), f"mma_in_din_{i}_{j}")
            din_in <<= din
            data_out_j_in = WireVector(len(data_out[j]), f"mma_in_data_out_{i}_{j}")
            data_out_j_in <<= data_out[j]
            switchin_in = WireVector(len(switchin), f"mma_in_switchin_{i}_{j}")
            switchin_in <<= switchin
            weights_in_last_j_in = WireVector(len(weights_in_last[j]), f"mma_in_weights_in_last_{i}_{j}")
            weights_in_last_j_in <<= weights_in_last[j]
            weights_enable_in = WireVector(len(weights_enable[j]), f"mma_in_weights_enable_{i}_{j}")
            weights_enable_in <<= weights_enable[j]
            weights_tag_in = WireVector(len(weights_tag[j]), f"mma_in_weights_tag_{i}_{j}")
            weights_tag_in <<= weights_tag[j]
            
            acc_out, din, switchin, newweight, newwe, newtag \
                = MAC(data_width, matrix_size, din, data_out[j], switchin, 
                    #   weights_in_last[j], 
                      cells[i][j], # using the cell from buf4 - way easier
                      weights_enable[j], weights_tag[j],
                      BITWIDTH, i, j)
            #probe(data_out[j], "MACacc{}_{}".format(i, j))
            #probe(acc_out, "MACout{}_{}".format(i, j))
            #probe(din, "MACdata{}_{}".format(i, j))
            acc_out_wv = WireVector(len(acc_out), f"mma_out_acc_out_{i}_{j}")
            acc_out_wv <<= acc_out
            din_wv = WireVector(len(acc_out), f"mma_out_din_{i}_{j}")
            din_wv <<= din
            switchin_wv = WireVector(len(acc_out), f"mma_out_switchin_{i}_{j}")
            switchin_wv <<= switchin
            newweight_wv = WireVector(len(acc_out), f"mma_out_newweight_{i}_{j}")
            newweight_wv <<= newweight
            newwe_wv = WireVector(len(acc_out), f"mma_out_newwe_{i}_{j}")
            newwe_wv <<= newwe
            newtag_wv = WireVector(len(acc_out), f"mma_out_newtag_{i}_{j}")
            newtag_wv <<= newtag
            weights_in_last[j] = newweight
            weights_enable[j] = newwe
            weights_tag[j] = newtag
            data_out[j] = acc_out

    return [ x.sign_extended(BITWIDTH) for x in data_out ]


def accum(acc_mem, size, data_in, waddr, wen, wclear, raddr, lastvec, index, 
          BITWIDTH):
    '''A single BITWIDTH-bit accumulator with 2^size BITWIDTH-bit buffers.
    On wen, writes data_in to the specified address (waddr) if wclear is high;
    otherwise, it performs an accumulate at the specified address (buffer[waddr] += data_in).
    lastvec is a control signal indicating that the operation being stored now is the
    last vector of a matrix multiply instruction (at the final accumulator, this becomes
    a "done" signal).
    '''
    wen_wv = WireVector(len(wen), f"accum_wen_wv_{index}")
    wen_wv <<= wen
    wclear_wv = WireVector(len(wclear), f"accum_wclear_wv_{index}")
    wclear_wv <<= wclear
    waddr_wv = WireVector(len(waddr), f"accum_waddr_wv_{index}")
    waddr_wv <<= waddr
    data_in_wv = WireVector(len(data_in), f"accum_data_in_wv_{index}")
    data_in_wv <<= data_in

    acc_mem_at_waddr = WireVector(len(acc_mem[waddr]), f"accum_acc_mem_at_waddr_{index}")
    acc_mem_at_waddr <<= acc_mem[waddr]

    acc_mem_no_overwrite = WireVector(len(acc_mem[waddr]), f"accum_acc_mem_no_overwrite_{index}")
    acc_mem_no_overwrite <<= (data_in + acc_mem[waddr])[:acc_mem.bitwidth]

    # Writes
    with conditional_assignment:
        with wen:
            with wclear:
                acc_mem[waddr] |= data_in
            with otherwise:
                acc_mem[waddr] |= acc_mem_no_overwrite

    # Read
    data_out = WireVector(BITWIDTH, f"accum_data_out_{index}")
    data_out <<= acc_mem[raddr]

    # Pipeline registers
    waddrsave = Register(len(waddr), f"accum_waddrsave_{index}")
    waddrsave.next <<= waddr
    wensave = Register(1, f"accum_wensave_{index}")
    wensave.next <<= wen
    wclearsave = Register(1, f"accum_wclearsave_{index}")
    wclearsave.next <<= wclear
    lastsave = Register(1, f"accum_lastsave_{index}")
    lastsave.next <<= lastvec

    return data_out, waddrsave, wensave, wclearsave, lastsave

def accumulators(acc_mems, accsize, datas_in, waddr, we, wclear, raddr, lastvec,
                 BITWIDTH):
    '''
    Produces array of accumulators of same dimension as datas_in.
    '''

    #probe(we, "accum_wen")
    #probe(wclear, "accum_wclear")
    #probe(waddr, "accum_waddr")

    accout = [ None for i in range(len(datas_in)) ]
    waddrin = waddr
    wein = we
    wclearin = wclear
    lastvecin = lastvec
    for i,x in enumerate(datas_in):
        #probe(x, "acc_{}_in".format(i))
        #probe(wein, "acc_{}_we".format(i))
        #probe(waddrin, "acc_{}_waddr".format(i))
        wein_before = WireVector(len(wein), f"accumulators_wein_before_{i}")
        wein_before <<= wein
        dout, waddrin, wein, wclearin, lastvecin = accum(acc_mems[i], accsize, x, 
                                                         waddrin, wein, wclearin, 
                                                         raddr, lastvecin, i, 
                                                         BITWIDTH)
        wein_after = WireVector(len(wein), f"accumulators_wein_after_{i}")
        wein_after <<= wein
        accout[i] = dout
        done = lastvecin

    return accout, done


def FIFO(mem_data, mem_valid, advance_fifo, MATSIZE, DWIDTH):
    '''
    matsize is the length of one row of the Matrix.
    mem_data is the connection from the DRAM controller, which is assumed to be 64 bytes wide.
    mem_valid is a one bit control signal from the controller indicating that the read completed and the current value is valid.
    advance_fifo signals to drop the tile at the end of the FIFO and advance everything forward.

    Output
    tile, ready, full
    tile: entire tile at the front of the queue (8 x matsize x matsize bits)
    ready: the tile output is valid
    full: there is no room in the FIFO
    '''

    #probe(mem_data, "fifo_dram_in")
    #probe(mem_valid, "fifo_dram_valid")
    #probe(advance_fifo, "weights_advance_fifo")
    
    # Make some size parameters, declare state register
    totalsize = int (MATSIZE * MATSIZE * DWIDTH / 8) # total size of a tile in bytes
    tilesize = totalsize * 8  # total size of a tile in bits
    ddrwidth = int(8 * DWIDTH)  # width from DDR in bytes (typically 64)
    # ddrwidth = int(len(mem_data) * DWIDTH / 64)  # width from DDR in bytes (typically 64)
    size = 1
    while pow(2, size) < (totalsize/ddrwidth):  # compute log of number of transfers required
        size = size + 1
    state = Register(size, "fifo_state")  # Number of reads to receive (each read is ddrwidth bytes)
    # print(f"DWIDTH = {DWIDTH}, len(state) = {len(state)}")
    state_wv = WireVector(len(state), "fifo_state_wv")
    state_wv <<= state
    mem_valid_wv = WireVector(len(mem_valid), "fifo_mem_valid_wv")
    mem_valid_wv <<= mem_valid
    startup = Register(1, "fifo_startup")
    startup.next <<= 1

    #probe(state, "fifo_state")
    
    # Declare top row of buffer: need to write to it in ddrwidth-byte chunks
    topbuf = [ Register(ddrwidth*8, f"fifo_topbuf_{i}") for i in range(max(1, int(totalsize/ddrwidth))) ]

    # Latch command to advance FIFO, since it may not complete immediately
    droptile = Register(1, "fifo_droptile")
    clear_droptile = WireVector(1, "fifo_clear_droptile")
    with conditional_assignment:
        with advance_fifo:
            droptile.next |= 1
        with clear_droptile:
            droptile.next |= 0

    #probe(droptile, "fifo_droptile")
    #probe(clear_droptile, "fifo_clear_droptile")
    
    # When we get data from DRAM controller, write to next buffer space
    with conditional_assignment:
        with mem_valid:
            state.next |= state + 1  # state tracks which ddrwidth-byte chunk we're writing to
            for i, reg in enumerate(reversed(topbuf)):  # enumerate a decoder for write-enable signals
                #probe(reg, "fifo_reg{}".format(i))
                with state == Const(i, bitwidth=size):
                    reg.next |= mem_data
        with otherwise:
            state.next |= 0  # reset state when no data is coming in (potential 8x8 matrix fix?)

    # Track when first buffer is filled and when data moves out of it
    full = Register(1, "fifo_full")  # goes high when last chunk of top buffer is filled
    cleartop = WireVector(1, "fifo_cleartop")
    with conditional_assignment:
        with mem_valid & (state == Const(len(topbuf)-1)):  # writing the last buffer spot now - likely have to change this
            full.next |= 1
        with cleartop:  # advancing FIFO, so buffer becomes empty
            full.next |= 0

    # Build buffers for remainder of FIFO
    buf2 = Register(tilesize, "fifo_buf2")
    buf3 = Register(tilesize, "fifo_buf3")
    buf4 = Register(tilesize, "fifo_buf4")
    #probe(concat_list(topbuf), "buf1")
    #probe(buf2, "buf2")
    #probe(buf3, "buf3")
    #probe(buf4, "buf4")
    #probe(full, "buf1_full")
    # If a given row is empty, track that so we can fill immediately
    empty2 = Register(1, "fifo_empty2")
    empty3 = Register(1, "fifo_empty3")
    empty4 = Register(1, "fifo_empty4")
    #probe(empty2, "buf2_empty")
    #probe(empty3, "buf3_empty")
    #probe(empty4, "buf4_empty")

    # Handle moving data between the buffers
    with conditional_assignment:
        with ~startup:
            empty2.next |= 1
            empty3.next |= 1
            empty4.next |= 1
        with full & empty2:  # First buffer is full, second is empty
            buf2.next |= concat_list(topbuf)  # move data to second buffer
            cleartop |= 1  # empty the first buffer
            empty2.next |= 0  # mark the second buffer as non-empty
        with empty3 & ~empty2:  # Third buffer is empty and second is full
            buf3.next |= buf2
            empty3.next |= 0
            empty2.next |= 1
        with empty4 & ~empty3:  # Fourth buffer is empty and third is full
            buf4.next |= buf3
            empty4.next |= 0
            empty3.next |= 1
        with droptile:
            empty4.next |= 1  # mark fourth buffer as free; tiles will advance automatically
            clear_droptile |= 1
    
    ready = startup & (~empty4) & (~droptile)  # there is data in final buffer and we're not about to change it

    return buf4, buf3, buf2, topbuf, ready, full

def systolic_setup(data_width, matsize, vec_in, waddr, valid, clearbit, lastvec, switch):
    '''Buffers vectors from the unified SRAM buffer so that they can be fed along diagonals to the
    Matrix Multiply array.

    matsize: row size of Matrix
    vec_in: row read from unified buffer
    waddr: the accumulator address this vector is bound for
    valid: this is a valid vector; write it when done
    clearbit: if 1, store result (default accumulate)
    lastvec: this is the last vector of a matrix
    switch: use the next weights tile beginning with this vector

    Output
    next_row: diagonal cross-cut of vectors to feed to MM array
    switchout: switch signals for MM array
    addrout: write address for first accumulator
    weout: write enable for first accumulator
    clearout: clear signal for first accumulator
    doneout: done signal for first accumulator
    '''
    # print(f"systolic_setup({data_width}, {matsize}, {len(vec_in)}, {len(waddr)}, \
    #        {len(valid)}, {len(clearbit)}, {len(lastvec)}, {len(switch)})")
    # Use a diagonal set of buffer so that when a vector is read from SRAM, it "falls" into
    # the correct diagonal pattern.
    # The last column of buffers need extra bits for control signals, which propagate down
    # and into the accumulators.

    sys_vec_in = WireVector(len(vec_in), "sys_vec_in")
    sys_vec_in <<= vec_in
    sys_waddr = WireVector(len(waddr), "sys_waddr")
    sys_waddr <<= waddr
    sys_valid = WireVector(1, "sys_valid")
    sys_valid <<= valid
    sys_clearbit = WireVector(1, "sys_clearbit")
    sys_clearbit <<= clearbit
    sys_lastvec = WireVector(1, "sys_lastvec")
    sys_lastvec <<= lastvec
    sys_switch = WireVector(1, "sys_switch")
    sys_switch <<= switch

    addrreg = Register(len(waddr), "sys_addrreg")
    addrreg.next <<= waddr
    wereg = Register(1, "sys_wereg")
    wereg.next <<= valid
    clearreg = Register(1, "sys_clearreg")
    clearreg.next <<= clearbit
    donereg = Register(1, "sys_donereg")
    donereg.next <<= lastvec
    topreg = Register(data_width, "sys_topreg")

    firstcolumn = [topreg,] + [ Register(data_width, f"sys_firstcolumn_{i}") for i in range(1, matsize) ]
    lastcolumn = [ None for i in range(matsize) ]
    lastcolumn[0] = topreg

    # Generate switch signals to matrix; propagate down
    switchout = [ None for i in range(matsize) ]
    switchout[0] = Register(1, "sys_switchout_0")
    switchout[0].next <<= switch
    for i in range(1, len(switchout)):
        switchout[i] = Register(1, f"sys_switchout_{i}")
        switchout[i].next <<= switchout[i-1]

    # Generate control pipeline for address, clear, and done signals
    addrout = addrreg
    addrout.name = "sys_addrout"
    weout = wereg
    weout.name = "sys_weout"
    clearout = clearreg
    clearout.name = "sys_clearout"
    doneout = lastvec
    doneout.name = "sys_doneout"
    #probe(clearout, "sys_clear_in")
    # Need one extra cycle of delay for control signals before giving them to first accumulator
    # But we already did registers for first row, so cancels out
    for i in range(0, matsize):
        a = Register(len(addrout), f"sys_a_{i}")
        a.next <<= addrout
        addrout = a
        w = Register(1, f"sys_w_{i}")
        w.next <<= weout
        weout = w
        c = Register(1, f"sys_c_{i}")
        c.next <<= clearout
        clearout = c
        d = Register(1, f"sys_d_{i}")
        d.next <<= doneout
        doneout = d
    #probe(clearout, "sys_clear_out")

    # Generate buffers in a diagonal pattern
    for row in range(1, matsize):  # first row is done
        left = firstcolumn[row]
        lastcolumn[row] = left
        for column in range(0, row):  # first column is done
            buf = Register(data_width, f"sys_buf_{row}_{column}")
            buf.next <<= left
            left = buf
            lastcolumn[row] = left  # holds final column for output

    # Connect first column to input data
    datain = [ vec_in[i*data_width : i*data_width+data_width] for i in range(matsize) ]
    for din, reg in zip(datain, firstcolumn):
        reg.next <<= din
    
    for i in range(len(lastcolumn)):
        sys_lastcolumn_i = WireVector(len(lastcolumn[i]), f"sys_lastcolumn_{i}")
        sys_lastcolumn_i <<= lastcolumn[i]

    return lastcolumn, switchout, addrout, weout, clearout, doneout


def MMU(acc_mems, data_width, matrix_size, accum_size, vector_in, accum_raddr, 
        accum_waddr, vec_valid, accum_overwrite, lastvec, switch_weights, 
        ddr_data, ddr_valid, nvecs_reg, MATSIZE, DWIDTH):  #, weights_in, weights_we):
    
    logn1 = 1
    while pow(2, logn1) < (matrix_size + 1):
        logn1 = logn1 + 1
    logn = 1
    while pow(2, logn) < (matrix_size):
        logn = logn + 1

    programming = Register(1, "mmu_programming")  # if high, we're programming new weights now
    waiting = WireVector(1, "mmu_waiting")  # if high, a switch is underway and we're waiting
        
    weights_wait = Register(logn1, "weights_wait")  # counts cycles since last weight push
    weights_count = Register(logn, "weights_count")  # counts cycles of current weight push
    startup = Register(1, "mmu_startup")
    startup.next <<= 1  # 0 only in first cycle
    weights_we = WireVector(1, "mmu_weights_we")
    done_programming = WireVector(1, "mmu_done_programming")
    first_tile = Register(1, "mmu_first_tile")  # Tracks if we've programmed the first tile yet

    #rtl_assert(~(switch_weights & (weights_wait != 0)), Exception("Weights are not ready to switch. Need a minimum of {} + 1 cycles since last switch.".format(matrix_size)))

    # advance FIFO after an MMC.S is finished with the front weight.
    # don't advance FIFO just because an RW instruction is finished
    acc_done_countdown = Register(32, "mmu_acc_done_countdown")
    advance_fifo = WireVector(1, "mmu_advance_fifo")

    # if an MMC.S came through, set the countdown to L + 2N, the duration 
    # between an MMC.S issue and the last change in the accumulator.
    # this might break if L + 2N was something tiny like 1 or 2, but that would
    # be silly
    with conditional_assignment:
        with switch_weights:
            acc_done_countdown.next |= nvecs_reg + Const(2 * matrix_size)
        with acc_done_countdown > 0:
            acc_done_countdown.next |= acc_done_countdown - 1
    
    # once the accumulator is done, the countdown will reach 1, and we can 
    # safely advance the FIFO.
    with conditional_assignment:
        with acc_done_countdown == 1:
            advance_fifo |= 1
        with otherwise:
            advance_fifo |= 0

    # FIFO
    buf4, buf3, buf2, buf1_list, tile_ready, full = FIFO(mem_data=ddr_data, 
                                                    mem_valid=ddr_valid, 
                                                    advance_fifo=advance_fifo,
                                                    MATSIZE=MATSIZE,
                                                    DWIDTH=DWIDTH) # advance fifo after an MMC.S is finished with the front weight. 
                                                  # advance_fifo=done_programming)
    #probe(tile_ready, "tile_ready")
    #probe(weights_tile, "FIFO_weights_out")
    
    matin, switchout, addrout, weout, clearout, doneout = \
        systolic_setup(data_width=data_width, matsize=matrix_size, 
                       vec_in=vector_in, waddr=accum_waddr, valid=vec_valid, 
                       clearbit=accum_overwrite, lastvec=lastvec, 
                       switch=switch_weights)

    mouts = MMArray(data_width=data_width, matrix_size=matrix_size, 
                    data_in=matin, new_weights=switchout, 
                    weights_in=buf4, weights_we=weights_we, BITWIDTH=DWIDTH)
    
    for i in range(len(mouts)):
        mouts_i = WireVector(len(mouts[i]), f"mmu_mouts_{i}")
        mouts_i <<= mouts[i]

    accout, done = accumulators(acc_mems=acc_mems, accsize=accum_size, 
                                datas_in=mouts, waddr=addrout, we=weout, 
                                wclear=clearout, raddr=accum_raddr, 
                                lastvec=doneout, BITWIDTH=data_width)

    switchstart = switchout[0]
    totalwait = Const(matrix_size + 1)
    waiting <<= weights_wait != totalwait  # if high, we have to wait 

    #probe(waiting, "waiting")
    
    with conditional_assignment:
        with ~startup:  # when we start, configure values to be ready to accept a new tile
            weights_wait.next |= totalwait
        with waiting:  # need to wait for switch to finish propagating
            weights_wait.next |= weights_wait + 1
        with ~first_tile & tile_ready:  # start programming the first tile
            weights_wait.next |= totalwait  # we don't have to swait for a switch to clear
            programming.next |= 1  # begin programming weights
            weights_count.next |= 0
            first_tile.next |= 1
        with switchstart:  # Weight switch initiated; begin waiting
            weights_wait.next |= 0
            programming.next |= 1
            weights_count.next |= 0
        with programming:  # We're pushing new weights now
            with weights_count == Const(matrix_size-1):  # We've reached the end
                programming.next |= 0
                done_programming |= 1
            with otherwise:  # Still programming; increment count and keep write signal high
                weights_count.next |= weights_count + 1
                weights_we |= 1
        
    '''
    with conditional_assignment:
        with startup == 0:  # When we start, we're ready to push weights as soon as FIFO is ready
            weights_wait.next |= totalwait
        with switchout:  # Got a switch signal; start wait count
            weights_wait.next |= 1  
        with weights_wait != totalwait:  # Stall on the final number
            weights_wait.next |= weights_wait + 1
        with weights_count != 0:  # If we've started programming new weights, reset
            weights_wait.next |= 0
        with otherwise:
            pass

        with ~startup:
            pass
        with (weights_wait == totalwait) & tile_ready:  # Ready to push new weights in
            weights_count.next |= 1
        with weights_count == Const(matrix_size):  # Finished pushing new weights
            done_programming |= 1
            weights_count.next |= 0
        with otherwise:  # We're pushing weights now; increment count
            weights_count.next |= weights_count + 1
            weights_we |= 1
    '''

    return accout, done, buf4, buf3, buf2, buf1_list

def MMU_top(acc_mems, data_width, matrix_size, accum_size, ub_size, start, 
            start_addr, nvecs, dest_acc_addr, overwrite, swap_weights, ub_rdata,
            accum_raddr, weights_dram_in, weights_dram_valid, MATSIZE, DWIDTH,
            HAZARD_DETECTION):
    '''

    Outputs
    ub_raddr: read address for unified buffer
    '''

    #probe(ub_rdata, "ub_mm_rdata")
    
    accum_waddr = Register(accum_size, "mmu_top_accum_waddr")
    vec_valid = WireVector(1, "mmu_top_vec_valid")
    overwrite_reg = Register(1, "mmu_top_overwrite_reg")
    last = WireVector(1, "mmu_top_last")
    swap_reg = Register(1, "mmu_top_swap_reg")

    # this busy signal is only tracking business for reading rows from UB. 
    # the whole MMC is busy for much longer.
    busy = Register(1, "busy_matrix")
    N = Register(len(nvecs), "mmu_top_N")
    ub_raddr = Register(ub_size, "mmu_top_ub_raddr")

    # rtl_assert(~(start & busy), Exception("Cannot dispatch new MM instruction while previous instruction is still being issued."))

    #probe(vec_valid, "MM_vec_valid_issue")
    #probe(busy, "MM_busy")
    # probe(accum_waddr, "accum_waddr")
    accum_waddr_wv = WireVector(accum_size, "accum_waddr_MMU")
    accum_waddr_wv <<= accum_waddr
    # probe(vec_valid, "vec_valid")
    # probe(overwrite_reg, "overwrite_reg")
    overwrite_wv = WireVector(1, "overwrite_MMU")
    overwrite_wv <<= overwrite_reg
    
    # Vector issue control logic
    with conditional_assignment:
        with start:  # new instruction being issued
            accum_waddr.next |= dest_acc_addr
            overwrite_reg.next |= overwrite
            swap_reg.next |= swap_weights
            busy.next |= 1
            N.next |= nvecs
            ub_raddr.next |= start_addr  # begin issuing next cycle
        with busy:  # We're issuing a vector this cycle
            vec_valid |= 1
            swap_reg.next |= 0
            N.next |= N - 1
            with N == 1:  # this was the last vector
                last |= 1
                overwrite_reg.next |= 0
                busy.next |= 0
            with otherwise:  # we're going to issue a vector next cycle as well
                ub_raddr.next |= ub_raddr + 1
                accum_waddr.next |= accum_waddr + 1
                last |= 0
        
    acc_out, done, buf4, buf3, buf2, buf1 = MMU(acc_mems=acc_mems, 
        data_width=data_width, matrix_size=matrix_size, accum_size=accum_size, 
        vector_in=ub_rdata, accum_raddr=accum_raddr, accum_waddr=accum_waddr, 
        vec_valid=vec_valid, accum_overwrite=overwrite_reg, lastvec=last, 
        switch_weights=swap_reg, ddr_data=weights_dram_in, 
        ddr_valid=weights_dram_valid, nvecs_reg=N, MATSIZE=MATSIZE, 
        DWIDTH=DWIDTH)

    #probe(ub_raddr, "ub_mm_raddr")

    return ub_raddr, acc_out, buf4, buf3, buf2, buf1

    

'''
Do we need full/stall signal from Matrix? Would need to stop SRAM out from writing to systolic setup
Yes: MMU needs to track when both buffers used and emit such a signal

The timing systems for weights programming are wonky right now. Both rtl_asserts are failing, but the
right answer comes out if you ignore that. It looks like the state machine that counts time since the
last weights programming keeps restarting, so the MMU thinks it's always programming weights?

Control signals propagating down systolic_setup to accumulators:
-Overwrite signal (default: accumulate)
-New accumulator address value (default: add 1 to previous address)
-Done signal?
'''

def testall(input_vectors, weights_vectors):
    DATWIDTH = 8
    MATSIZE = 4
    ACCSIZE = 8

    L = len(input_vectors)
    
    ins = [probe(Input(DATWIDTH)) for i in range(MATSIZE)]
    invec = concat_list(ins)
    swap = Input(1, 'swap')
    waddr = Input(8)
    lastvec = Input(1)
    valid = Input(1)
    raddr = Input(8, "raddr")  # accumulator read address to read out answers
    donesig = Output(1, "done")

    outs = [Output(32, name="out{}".format(str(i))) for i in range(MATSIZE)]

    #ws = [ Const(item, bitwidth=DATWIDTH) for sublist in weights_vectors for item in sublist ]  # flatten weight matrix
    #ws = concat_list(ws)  # combine weights into single wire
    ws = [ item for sublist in weights_vectors for item in sublist ]  # flatten weight matrix
    # print(ws)
    #ws = reduce(lambda x, y : (x<<8)+y, ws)  # "concat" weights into one integer
    
    weightsdata = Input(64*8)
    weightsvalid = Input(1)
    
    accout, done, buf4, buf3, buf2, buf1 = MMU(data_width=DATWIDTH, 
        matrix_size=MATSIZE, accum_size=ACCSIZE, vector_in=invec, 
        accum_raddr=raddr, accum_waddr=waddr, vec_valid=valid, 
        accum_overwrite=Const(0), lastvec=lastvec, switch_weights=swap, 
        ddr_data=weightsdata, ddr_valid=weightsvalid)

    donesig <<= done
    for out, accout in zip(outs, accout):
        out <<= accout

    sim_trace = SimulationTrace()
    sim = FastSimulation(tracer=sim_trace)

    # make a default input dictionary
    din = { swap:0, waddr:0, lastvec:0, valid:0, raddr:0, weightsdata:0, weightsvalid:0 }
    din.update({ins[j] : 0 for j in range(MATSIZE)})

    # Give a few cycles for startup
    sim.step(din)
    
    # First, simulate memory read to feed weights to FIFO
    chunk = 64*8  # size of one dram read
    #ws = [ ws[i*chunk:i*chunk+chunk] for i in range(max(1,len(ws)/chunk)) ]  # divide weights into dram chunks
    # divide weights into dram-transfer sized chunks
    ws = reduce(lambda x, y : (x<<8)+y, ws)  # "concat" weights into one integer
    ws = [ (ws >> (64*8*i)) & pow(2, 64*8)-1 for i in range(max(1,len(weights_vectors)/64)) ]
    # print(ws)
    for block in ws:
        d = din.copy()
        d.update({ins[j] : 0 for j in range(MATSIZE)})
        d.update({ weightsdata:block, weightsvalid:1})
        sim.step(d)

    # Wait until the FIFO is ready
    for i in range(10):
        sim.step(din)
    
    #din.update({ins[j]:0 for j in range(MATSIZE)})
    
    # Send signal to write weights
    #d = din.copy()
    #d[weights_we] = 1
    #sim.step(d)

    # Wait MATSIZE cycles for weights to propagate
    for i in range(MATSIZE*2):
        sim.step(din)

    # Send the swap signal with first row of input
    d = din.copy()
    d.update({ins[j] : input_vectors[0][j] for j in range(MATSIZE) })
    d.update({ swap : 1, valid : 1 })
    sim.step(d)

    # Send rest of input
    for i in range(L-1):
        d = din.copy()
        d.update({ins[j] : input_vectors[i+1][j] for j in range(MATSIZE) })
        d.update({ waddr : i+1, lastvec : 1 if i == L-2 else 0, valid : 1 })
        sim.step(d)

    # Wait some cycles while it propagates
    for i in range(L*2):
        d = din.copy()
        sim.step(d)

    # Read out values
    for i in range(L):
        d = din.copy()
        d[raddr] = i
        sim.step(d)

    with open('trace.vcd', 'w') as f:
        sim_trace.print_vcd(f)


if __name__ == "__main__":
    #weights = [[1, 10, 10, 2], [3, 9, 6, 2], [6, 8, 2, 8], [4, 1, 8, 6]]  # transposed
    #weights = [[4, 1, 8, 6], [6, 8, 2, 8], [3, 9, 6, 2], [1, 10, 10, 2]]  # tranposed, reversed
    #weights = [[1, 3, 6, 4], [10, 9, 8, 1], [10, 6, 2, 8], [2, 2, 8, 6]]
    weights = [[2, 2, 8, 6], [10, 6, 2, 8], [10, 9, 8, 1], [1, 3, 6, 4]]  # reversed

    vectors = [[12, 7, 2, 6], [21, 21, 18, 8], [1, 4, 18, 11], [6, 3, 25, 15], 
               [21, 12, 1, 15], [1, 6, 13, 8], [24, 25, 18, 1], [2, 5, 13, 6], 
               [19, 3, 1, 17], [25, 10, 20, 10]]

    testall(vectors, weights)
