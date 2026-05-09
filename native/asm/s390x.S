/*
 * PysiAdmin — native/asm/s390x.S  v2.0
 */
    .section .note.GNU-stack,"",@progbits
    .text

    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    ltgr    %r3, %r3
    bzr     %r14
    lghi    %r0, 0
.Lsz_loop:
    stc     %r0, 0(%r2)
    la      %r2, 1(%r2)
    aghi    %r3, -1
    jnz     .Lsz_loop
    br      %r14
    .size pysi_secure_zero, .-pysi_secure_zero

    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    stck    0(%r15)
    lg      %r2, 0(%r15)
    br      %r14
    .size pysi_rdtsc, .-pysi_rdtsc

/*
 * int pysi_ct_compare(const void *a, const void *b, size_t n)
 * r2=a, r3=b, r4=n
 */
    .globl pysi_ct_compare
    .type  pysi_ct_compare, @function
pysi_ct_compare:
    lghi    %r5, 0
    ltgr    %r4, %r4
    bzr     %r14
.Lct_loop_s390:
    ic      %r6, 0(%r2)
    ic      %r7, 0(%r3)
    xr      %r6, %r7
    or      %r5, %r6
    la      %r2, 1(%r2)
    la      %r3, 1(%r3)
    aghi    %r4, -1
    jnz     .Lct_loop_s390
    lcr     %r5, %r5
    srl     %r5, 31
    lgfr    %r2, %r5
    br      %r14
    .size pysi_ct_compare, .-pysi_ct_compare

    .globl pysi_stack_guard
    .type  pysi_stack_guard, @function
pysi_stack_guard:
    br      %r14
    .size pysi_stack_guard, .-pysi_stack_guard
