/*
 * PysiAdmin — native/asm/riscv64.S
 * Secure memory helpers for RISC-V 64-bit.
 */
    .section .note.GNU-stack,"",@progbits
    .text

/*
 * void pysi_secure_zero(void *ptr, size_t n)
 * a0 = ptr, a1 = n
 */
    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    beqz    a1, .Ldone
.Lloop:
    sb      zero, 0(a0)
    addi    a0, a0, 1
    addi    a1, a1, -1
    bnez    a1, .Lloop
.Ldone:
    ret
    .size pysi_secure_zero, .-pysi_secure_zero

/*
 * uint64_t pysi_rdtsc(void)
 * Read the RISC-V cycle CSR.
 */
    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    rdcycle a0
    ret
    .size pysi_rdtsc, .-pysi_rdtsc
