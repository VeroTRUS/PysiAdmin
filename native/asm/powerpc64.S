/*
 * PysiAdmin — native/asm/powerpc64.S  v2.0
 */
    .section .note.GNU-stack,"",@progbits
    .text

    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    cmpdi   %r4, 0
    beqlr
.Lsz_loop:
    stb     0, 0(%r3)
    addi    %r3, %r3, 1
    addi    %r4, %r4, -1
    cmpdi   %r4, 0
    bne     .Lsz_loop
    blr
    .size pysi_secure_zero, .-pysi_secure_zero

    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    mftb    %r3
    blr
    .size pysi_rdtsc, .-pysi_rdtsc

/*
 * int pysi_ct_compare(const void *a, const void *b, size_t n)
 * r3=a, r4=b, r5=n
 */
    .globl pysi_ct_compare
    .type  pysi_ct_compare, @function
pysi_ct_compare:
    li      %r6, 0              /* accumulator */
    cmpdi   %r5, 0
    beq     .Lct_done_ppc
.Lct_loop_ppc:
    lbz     %r7, 0(%r3)
    lbz     %r8, 0(%r4)
    xor     %r7, %r7, %r8
    or      %r6, %r6, %r7
    addi    %r3, %r3, 1
    addi    %r4, %r4, 1
    addi    %r5, %r5, -1
    cmpdi   %r5, 0
    bne     .Lct_loop_ppc
.Lct_done_ppc:
    neg     %r3, %r6
    srwi    %r3, %r3, 31
    blr
    .size pysi_ct_compare, .-pysi_ct_compare

    .globl pysi_stack_guard
    .type  pysi_stack_guard, @function
pysi_stack_guard:
    blr
    .size pysi_stack_guard, .-pysi_stack_guard
