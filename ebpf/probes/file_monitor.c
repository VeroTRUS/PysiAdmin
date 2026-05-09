/*
 * PysiAdmin — ebpf/probes/file_monitor.c
 *
 * Traces openat(2) calls touching sensitive paths.
 * Only emits an event when the filename contains a monitored prefix —
 * filtering in-kernel keeps perf buffer traffic minimal.
 *
 * Kernel: Linux 4.7+
 */

#include <linux/sched.h>

struct file_event_t {
    u64  timestamp_ns;
    u32  pid;
    u32  uid;
    int  flags;
    char comm[TASK_COMM_LEN];
    char filename[256];
};

BPF_PERF_OUTPUT(file_events);

/*
 * Sensitive path prefixes to watch. Kernel BPF cannot call strstr(),
 * so we check the first few bytes against known prefixes.
 */
static __always_inline int is_sensitive(const char *path)
{
    /* /etc/ */
    if (path[0]=='/' && path[1]=='e' && path[2]=='t' && path[3]=='c' && path[4]=='/')
        return 1;
    /* /root/ */
    if (path[0]=='/' && path[1]=='r' && path[2]=='o' && path[3]=='o' && path[4]=='t')
        return 1;
    /* /boot/ */
    if (path[0]=='/' && path[1]=='b' && path[2]=='o' && path[3]=='o' && path[4]=='t')
        return 1;
    /* /proc/kcore */
    if (path[0]=='/' && path[1]=='p' && path[2]=='r' && path[3]=='o' && path[4]=='c')
        return 1;
    /* /sys/firmware */
    if (path[0]=='/' && path[1]=='s' && path[2]=='y' && path[3]=='s' && path[4]=='/')
        return 1;
    return 0;
}

TRACEPOINT_PROBE(syscalls, sys_enter_openat)
{
    char filename[256] = {};
    bpf_probe_read_user_str(filename, sizeof(filename), args->filename);

    if (!is_sensitive(filename))
        return 0;

    struct file_event_t ev = {};
    ev.timestamp_ns = bpf_ktime_get_ns();
    ev.pid          = bpf_get_current_pid_tgid() >> 32;
    ev.uid          = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    ev.flags        = args->flags;

    bpf_get_current_comm(&ev.comm, sizeof(ev.comm));
    __builtin_memcpy(ev.filename, filename, sizeof(ev.filename));

    file_events.perf_submit(args, &ev, sizeof(ev));
    return 0;
}
