/*
 * PysiAdmin — native/asm_wrapper.c
 * C wrapper over arch-specific assembly routines.
 * Compiled into libpysiasm.so and loaded by core/crypto.py via ctypes.
 */

#include <stddef.h>
#include <stdint.h>

extern void     pysi_secure_zero(void *ptr, size_t n);
extern uint64_t pysi_rdtsc(void);

/*
 * pysi_secure_wipe(ptr, n)
 * Public symbol — zeroes n bytes, guaranteed not optimized away.
 */
void pysi_secure_wipe(void *ptr, size_t n)
{
    pysi_secure_zero(ptr, n);
}

/*
 * pysi_timing_now()
 * Architecture-agnostic timing counter.
 */
uint64_t pysi_timing_now(void)
{
    return pysi_rdtsc();
}
