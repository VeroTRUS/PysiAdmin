/*
 * PysiAdmin — ebpf/probes/exec_monitor.c
 *
 * Traces execve(2) system calls system-wide via a tracepoint.
 * Tracepoints fire after the kernel has copied syscall arguments into
 * kernelspace, so bpf_probe_read_kernel_str() reliably captures the
 * filename — unlike the old kprobe approach which raced against that copy.
 *
 * Loaded by ebpf/monitor.py via python3-bcc.
 * Kernel requirement: Linux 4.7+ (BPF tracepoint support)
 *
 * Tracepoint: syscalls/sys_enter_execve
 * Format:     /sys/kernel/tracing/events/syscalls/sys_enter_execve/format
 */

#include <linux/sched.h>
#include <uapi/linux/limits.h>   /* PATH_MAX = 4096 */

/* ── Event structure sent to userspace via perf ring buffer ─────────────── */
struct exec_event_t {
    u32  pid;
    u32  ppid;
    u32  uid;
    char comm[TASK_COMM_LEN];  /* name of the calling process, max 16 chars  */
    char filename[256];        /* path passed to execve, capped at 255 + NUL */
};

BPF_PERF_OUTPUT(exec_events);

/*
 * TRACEPOINT_PROBE(category, event) expands to a BCC tracepoint handler.
 * The `args` struct mirrors the tracepoint format fields:
 *   args->filename  — const char __user * (already staged in kernelspace
 *                     by the time the tracepoint fires on entry)
 *   args->argv      — const char __user *const __user *
 *   args->envp      — const char __user *const __user *
 */
TRACEPOINT_PROBE(syscalls, sys_enter_execve)
{
    struct exec_event_t ev = {};
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();

    ev.pid  = bpf_get_current_pid_tgid() >> 32;
    ev.uid  = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    ev.ppid = task->real_parent->tgid;

    bpf_get_current_comm(&ev.comm, sizeof(ev.comm));

    /*
     * args->filename is a userspace pointer, but BCC's tracepoint staging
     * means it's safe to read with bpf_probe_read_user_str here.
     * We cap at 255 bytes (+ NUL) to stay well within the BPF stack limit.
     */
    bpf_probe_read_user_str(ev.filename, sizeof(ev.filename), args->filename);

    exec_events.perf_submit(args, &ev, sizeof(ev));
    return 0;
}
