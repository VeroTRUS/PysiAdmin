/*
 * PysiAdmin — ebpf/probes/exec_monitor.c
 *
 * Traces execve(2) via tracepoint. Added in 0.1.5:
 *   - Per-PID rate limiting: at most RATE_LIMIT_MAX events per PID
 *     within RATE_LIMIT_NS nanoseconds, to prevent perf buffer flooding
 *     from tight exec loops (e.g. shell completion scripts, bwrap chains).
 *   - Noise filter: skip kernel threads (uid == 0 && comm starts with '(')
 *
 * Loaded by ebpf/monitor.py via python3-bcc.
 * Kernel: Linux 4.7+
 */

#include <linux/sched.h>

/* ── Rate limiting ─────────────────────────────────────────────────────────
 * Allow at most RATE_LIMIT_MAX events from the same PID within
 * RATE_LIMIT_NS nanoseconds (default: 5 events per 200 ms).
 */
#define RATE_LIMIT_NS   200000000ULL   /* 200 ms in nanoseconds */
#define RATE_LIMIT_MAX  5

struct rate_entry_t {
    u64 window_start;   /* timestamp of first event in current window */
    u32 count;          /* events seen in this window                 */
};

BPF_HASH(rate_map, u32, struct rate_entry_t, 8192);

/* ── Event structure ───────────────────────────────────────────────────── */
struct exec_event_t {
    u64  timestamp_ns;
    u32  pid;
    u32  ppid;
    u32  uid;
    char comm[TASK_COMM_LEN];
    char filename[256];
};

BPF_PERF_OUTPUT(exec_events);

TRACEPOINT_PROBE(syscalls, sys_enter_execve)
{
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;

    /* ── Rate limit check ─────────────────────────────────────────────── */
    u64 now = bpf_ktime_get_ns();
    struct rate_entry_t zero = {};
    struct rate_entry_t *re  = rate_map.lookup_or_try_init(&pid, &zero);
    if (re) {
        if (now - re->window_start < RATE_LIMIT_NS) {
            re->count++;
            if (re->count > RATE_LIMIT_MAX)
                return 0;   /* drop event — too noisy */
        } else {
            re->window_start = now;
            re->count        = 1;
        }
    }

    /* ── Noise filter: skip kernel worker threads ─────────────────────── */
    char comm_peek[2] = {};
    bpf_get_current_comm(&comm_peek, sizeof(comm_peek));
    if (uid == 0 && comm_peek[0] == '(')
        return 0;

    /* ── Build and submit event ───────────────────────────────────────── */
    struct exec_event_t ev = {};
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();

    ev.timestamp_ns = now;
    ev.pid          = pid;
    ev.uid          = uid;
    ev.ppid         = task->real_parent->tgid;

    bpf_get_current_comm(&ev.comm, sizeof(ev.comm));
    bpf_probe_read_user_str(ev.filename, sizeof(ev.filename), args->filename);

    exec_events.perf_submit(args, &ev, sizeof(ev));
    return 0;
}
