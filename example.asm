// with %a = 2, %flag = 0
// result written to vector 1
module {
    func.func @branch(%a:i32, %flag:i1) -> (i32) {
    cf.cond_br %flag, ^bb1, ^bb2
    ^bb1:
        return %a : i32
    ^bb2:
        %0 = arith.addi %a, %a : i32
        return %0 : i32
    }
}