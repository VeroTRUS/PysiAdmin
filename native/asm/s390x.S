/*
 * PysiAdmin — native/asm/s390x.S
 * Secure memory helpers for IBM s390x (z/Architecture).
 */
    .section .note.GNU-stack,"",@progbits
    .text

/*
 * void pysi_secure_zero(void *ptr, size_t n)
 * r2 = ptr, r3 = n
 */
    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    ltgr    %r3, %r3
    bzr     %r14
    lghi    %r0, 0
.Lloop:
    stc     %r0, 0(%r2)
    la      %r2, 1(%r2)
    aghi    %r3, -1
    jnz     .Lloop
    br      %r14
    .size pysi_secure_zero, .-pysi_secure_zero

/*
 * uint64_t pysi_rdtsc(void)
 * Read the s390x Store Clock (STCK).
 */
    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    stck    0(%r15)
    lg      %r2, 0(%r15)
    br      %r14
    .size pysi_rdtsc, .-pysi_rdtsc
