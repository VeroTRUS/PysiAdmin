/*
 * PysiAdmin — native/asm/arm64.S
 * Secure memory helpers for AArch64 (ARM64).
 */
    .section .note.GNU-stack,"",@progbits
    .text

/*
 * void pysi_secure_zero(void *ptr, size_t n)
 * x0 = ptr, x1 = n
 */
    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    cbz     x1, .Ldone
.Lloop:
    strb    wzr, [x0], #1
    subs    x1, x1, #1
    bne     .Lloop
.Ldone:
    ret
    .size pysi_secure_zero, .-pysi_secure_zero

/*
 * uint64_t pysi_rdtsc(void)
 * Read the AArch64 virtual counter.
 */
    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    mrs     x0, cntvct_el0
    ret
    .size pysi_rdtsc, .-pysi_rdtsc
