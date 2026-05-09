/*
 * PysiAdmin — native/asm/arm64.S  v2.0
 */
    .section .note.GNU-stack,"",@progbits
    .text

    .globl pysi_secure_zero
    .type  pysi_secure_zero, @function
pysi_secure_zero:
    cbz     x1, .Lsz_done
.Lsz_loop:
    strb    wzr, [x0], #1
    subs    x1, x1, #1
    bne     .Lsz_loop
.Lsz_done:
    ret
    .size pysi_secure_zero, .-pysi_secure_zero

    .globl pysi_rdtsc
    .type  pysi_rdtsc, @function
pysi_rdtsc:
    mrs     x0, cntvct_el0
    ret
    .size pysi_rdtsc, .-pysi_rdtsc

/*
 * int pysi_ct_compare(const void *a, const void *b, size_t n)
 * x0=a, x1=b, x2=n  →  returns 0 (equal) or 1 (different)
 */
    .globl pysi_ct_compare
    .type  pysi_ct_compare, @function
pysi_ct_compare:
    mov     x3, xzr             /* accumulator = 0 */
    cbz     x2, .Lct_done_a64
.Lct_loop_a64:
    ldrb    w4, [x0], #1
    ldrb    w5, [x1], #1
    eor     w4, w4, w5
    orr     w3, w3, w4
    subs    x2, x2, #1
    bne     .Lct_loop_a64
.Lct_done_a64:
    /* normalize */
    neg     w3, w3
    lsr     w0, w3, #31
    ret
    .size pysi_ct_compare, .-pysi_ct_compare

    .globl pysi_stack_guard
    .type  pysi_stack_guard, @function
pysi_stack_guard:
    /* No hardware canary register on arm64 — no-op placeholder */
    ret
    .size pysi_stack_guard, .-pysi_stack_guard
