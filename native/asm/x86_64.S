/*
 * PysiAdmin — native/asm/x86_64.S
 * Secure memory helpers for x86_64 (AMD64 / Intel64).
 */
    .section .note.GNU-stack,"",@progbits   /* non-executable stack */
    .text

/*
 * void pysi_secure_zero(void *ptr, size_t n)
 * Zero n bytes at ptr using REP STOSB.
 * The volatile operand prevents the compiler from eliding this.
 */
    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    xor     %eax, %eax
    mov     %rsi, %rcx
    rep stosb
    ret
    .size pysi_secure_zero, .-pysi_secure_zero

/*
 * uint64_t pysi_rdtsc(void)
 * Read the hardware Time Stamp Counter.
 */
    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    rdtsc
    shl     $32, %rdx
    or      %rdx, %rax
    ret
    .size pysi_rdtsc, .-pysi_rdtsc
