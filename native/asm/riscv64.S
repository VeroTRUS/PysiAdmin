/*
 * PysiAdmin — native/asm/riscv64.S  v2.0
 */
    .section .note.GNU-stack,"",@progbits
    .text

    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    beqz    a1, .Lsz_done
.Lsz_loop:
    sb      zero, 0(a0)
    addi    a0, a0, 1
    addi    a1, a1, -1
    bnez    a1, .Lsz_loop
.Lsz_done:
    ret
    .size pysi_secure_zero, .-pysi_secure_zero

    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    rdcycle a0
    ret
    .size pysi_rdtsc, .-pysi_rdtsc

/*
 * int pysi_ct_compare(const void *a, const void *b, size_t n)
 * a0=a, a1=b, a2=n
 */
    .globl pysi_ct_compare
    .type  pysi_ct_compare, @function
pysi_ct_compare:
    li      t0, 0               /* accumulator */
    beqz    a2, .Lct_done_rv
.Lct_loop_rv:
    lbu     t1, 0(a0)
    lbu     t2, 0(a1)
    xor     t1, t1, t2
    or      t0, t0, t1
    addi    a0, a0, 1
    addi    a1, a1, 1
    addi    a2, a2, -1
    bnez    a2, .Lct_loop_rv
.Lct_done_rv:
    neg     t0, t0
    srli    a0, t0, 63
    ret
    .size pysi_ct_compare, .-pysi_ct_compare

    .globl pysi_stack_guard
    .type  pysi_stack_guard, @function
pysi_stack_guard:
    ret
    .size pysi_stack_guard, .-pysi_stack_guard
