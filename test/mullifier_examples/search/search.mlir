module {
  memref.global @edges : memref<10xi32> = dense<[1, 0, 2, 3, 1, 3, 1, 2, 4, 3]>
  memref.global @nodes : memref<6xi32> = dense<[0, 1, 4, 6, 9, 10]>
  memref.global @length : memref<5xi32> = dense<[0, -1, -1, -1, -1]>
  memref.global @to_visit_start : memref<1xi32> = dense<0>
  memref.global @to_visit_end : memref<1xi32> = dense<0>
  memref.global @to_visit : memref<5xi32> = uninitialized
  func.func @add_to_visit(%arg0: i32) -> i32 attributes {llvm.linkage = #llvm.linkage<external>} {
    %c0_i32 = arith.constant 0 : i32
    %c1_i32 = arith.constant 1 : i32
    %0 = memref.get_global @to_visit : memref<5xi32>
    %1 = memref.get_global @to_visit_end : memref<1xi32>
    %2 = affine.load %1[0] : memref<1xi32>
    %3 = arith.addi %2, %c1_i32 : i32
    affine.store %3, %1[0] : memref<1xi32>
    %4 = arith.index_cast %2 : i32 to index
    affine.store %arg0, %0[symbol(%4)] : memref<5xi32>
    return %c0_i32 : i32
  }
  func.func @get_top() -> i32 attributes {llvm.linkage = #llvm.linkage<external>} {
    %c1_i32 = arith.constant 1 : i32
    %0 = memref.get_global @to_visit : memref<5xi32>
    %1 = memref.get_global @to_visit_start : memref<1xi32>
    %2 = affine.load %1[0] : memref<1xi32>
    %3 = arith.addi %2, %c1_i32 : i32
    affine.store %3, %1[0] : memref<1xi32>
    %4 = arith.index_cast %2 : i32 to index
    %5 = affine.load %0[symbol(%4)] : memref<5xi32>
    return %5 : i32
  }
  func.func @search(%arg0: i32, %arg1: i32) -> i32 attributes {llvm.linkage = #llvm.linkage<external>} {
    %c1 = arith.constant 1 : index
    %c-1_i32 = arith.constant -1 : i32
    %c5_i32 = arith.constant 5 : i32
    %c1_i32 = arith.constant 1 : i32
    %0 = call @add_to_visit(%arg0) : (i32) -> i32
    %1 = memref.get_global @to_visit_start : memref<1xi32>
    %2 = memref.get_global @to_visit_end : memref<1xi32>
    %3 = memref.get_global @length : memref<5xi32>
    %4 = memref.get_global @nodes : memref<6xi32>
    scf.while : () -> () {
      %8 = affine.load %1[0] : memref<1xi32>
      %9 = affine.load %2[0] : memref<1xi32>
      %10 = arith.cmpi ne, %8, %9 : i32
      scf.condition(%10)
    } do {
      %8 = func.call @get_top() : () -> i32
      %9 = arith.index_cast %8 : i32 to index
      %10 = memref.load %3[%9] : memref<5xi32>
      %11 = memref.load %4[%9] : memref<6xi32>
      %12 = arith.addi %8, %c1_i32 : i32
      %13 = arith.index_cast %12 : i32 to index
      %14 = memref.load %4[%13] : memref<6xi32>
      %15 = arith.index_cast %14 : i32 to index
      %16 = arith.index_cast %11 : i32 to index
      scf.for %arg2 = %16 to %15 step %c1 {
        %17 = arith.subi %arg2, %16 : index
        %18 = arith.index_cast %11 : i32 to index
        %19 = arith.addi %18, %17 : index
        %20 = memref.get_global @edges : memref<10xi32>
        %21 = memref.load %20[%19] : memref<10xi32>
        %22 = arith.cmpi slt, %21, %c5_i32 : i32
        scf.if %22 {
          %23 = arith.index_cast %21 : i32 to index
          %24 = memref.load %3[%23] : memref<5xi32>
          %25 = arith.addi %10, %c1_i32 : i32
          %26 = arith.cmpi eq, %24, %c-1_i32 : i32
          scf.if %26 {
            memref.store %25, %3[%23] : memref<5xi32>
            %28 = func.call @add_to_visit(%21) : (i32) -> i32
          }
          %27 = arith.cmpi slt, %25, %24 : i32
          scf.if %27 {
            memref.store %25, %3[%23] : memref<5xi32>
          }
        }
      }
      scf.yield
    }
    %5 = memref.get_global @length : memref<5xi32>
    %6 = arith.index_cast %arg1 : i32 to index
    %7 = affine.load %5[symbol(%6)] : memref<5xi32>
    return %7 : i32
  }
  func.func @gpmm_main() -> i32 attributes {llvm.linkage = #llvm.linkage<external>} {
    %c3_i32 = arith.constant 3 : i32
    %c0_i32 = arith.constant 0 : i32
    %0 = call @search(%c0_i32, %c3_i32) : (i32, i32) -> i32
    return %0 : i32
  }
}
