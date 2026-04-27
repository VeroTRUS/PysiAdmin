/*
 * PysiAdmin — native/asm/powerpc64.S
 * Secure memory helpers for IBM POWER (ppc64le).
 */
    .section .note.GNU-stack,"",@progbits
    .text

/*
 * void pysi_secure_zero(void *ptr, size_t n)
 * r3 = ptr, r4 = n
 */
    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    cmpdi   %r4, 0
    beqlr
.Lloop:
    stb     0, 0(%r3)
    addi    %r3, %r3, 1
    addi    %r4, %r4, -1
    cmpdi   %r4, 0
    bne     .Lloop
    blr
    .size pysi_secure_zero, .-pysi_secure_zero

/*
 * uint64_t pysi_rdtsc(void)
 * Read the PowerPC timebase register.
 */
    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    mftb    %r3
    blr
    .size pysi_rdtsc, .-pysi_rdtsc
