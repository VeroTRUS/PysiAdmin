/*
 * PysiAdmin — ebpf/probes/priv_monitor.c
 *
 * Traces setresuid(2) and setresgid(2) — the primary mechanism
 * by which processes escalate privileges on Linux.
 * Emits an alert event any time a process attempts to set UID/GID to 0.
 *
 * Kernel: Linux 4.7+
 */

#include <linux/sched.h>

struct priv_event_t {
    u64  timestamp_ns;
    u32  pid;
    u32  current_uid;
    u32  target_ruid;
    u32  target_euid;
    u32  target_suid;
    char comm[TASK_COMM_LEN];
    u8   is_gid;     /* 0 = setresuid, 1 = setresgid */
};

BPF_PERF_OUTPUT(priv_events);

TRACEPOINT_PROBE(syscalls, sys_enter_setresuid)
{
    /* Only alert when trying to gain root (uid 0) */
    uid_t ruid = (uid_t)args->ruid;
    uid_t euid = (uid_t)args->euid;
    uid_t suid = (uid_t)args->suid;

    if (ruid != 0 && euid != 0 && suid != 0)
        return 0;

    struct priv_event_t ev = {};
    ev.timestamp_ns  = bpf_ktime_get_ns();
    ev.pid           = bpf_get_current_pid_tgid() >> 32;
    ev.current_uid   = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    ev.target_ruid   = ruid;
    ev.target_euid   = euid;
    ev.target_suid   = suid;
    ev.is_gid        = 0;

    bpf_get_current_comm(&ev.comm, sizeof(ev.comm));
    priv_events.perf_submit(args, &ev, sizeof(ev));
    return 0;
}

TRACEPOINT_PROBE(syscalls, sys_enter_setresgid)
{
    gid_t rgid = (gid_t)args->rgid;
    gid_t egid = (gid_t)args->egid;
    gid_t sgid = (gid_t)args->sgid;

    if (rgid != 0 && egid != 0 && sgid != 0)
        return 0;

    struct priv_event_t ev = {};
    ev.timestamp_ns  = bpf_ktime_get_ns();
    ev.pid           = bpf_get_current_pid_tgid() >> 32;
    ev.current_uid   = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    ev.target_ruid   = rgid;
    ev.target_euid   = egid;
    ev.target_suid   = sgid;
    ev.is_gid        = 1;

    bpf_get_current_comm(&ev.comm, sizeof(ev.comm));
    priv_events.perf_submit(args, &ev, sizeof(ev));
    return 0;
}
