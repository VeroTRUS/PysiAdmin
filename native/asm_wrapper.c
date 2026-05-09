/*
 * PysiAdmin — native/asm_wrapper.c  v2.0
 * Adds pysi_ct_compare and pysi_stack_guard exports.
 */

#include <stddef.h>
#include <stdint.h>

extern void     pysi_secure_zero(void *ptr, size_t n);
extern uint64_t pysi_rdtsc(void);
extern int      pysi_ct_compare(const void *a, const void *b, size_t n);
extern void     pysi_stack_guard(void);

void pysi_secure_wipe(void *ptr, size_t n)
{
    pysi_secure_zero(ptr, n);
}

uint64_t pysi_timing_now(void)
{
    return pysi_rdtsc();
}

/*
 * pysi_ct_memcmp(a, b, n) → 0 if equal, 1 if different.
 * Drop-in for timing-safe token comparison in core/crypto.py.
 */
int pysi_ct_memcmp(const void *a, const void *b, size_t n)
{
    return pysi_ct_compare(a, b, n);
}

void pysi_check_stack(void)
{
    pysi_stack_guard();
}
