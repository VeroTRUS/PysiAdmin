/*
 * PysiAdmin — ebpf/probes/net_monitor.c
 *
 * Traces outbound TCP/UDP connect(2) calls.
 * Records: pid, uid, destination address (IPv4 & IPv6), port, comm.
 * Useful for detecting unexpected network activity on the host.
 *
 * Loaded by ebpf/monitor.py alongside exec_monitor.c.
 * Kernel: Linux 4.7+
 */

#include <linux/sched.h>
#include <linux/socket.h>
#include <linux/in.h>
#include <linux/in6.h>
#include <uapi/linux/un.h>

/* ── Event structure ───────────────────────────────────────────────────── */
#define AF_INET  2
#define AF_INET6 10

struct net_event_t {
    u64  timestamp_ns;
    u32  pid;
    u32  uid;
    u16  family;             /* AF_INET or AF_INET6          */
    u16  dport;              /* destination port, host order */
    u8   daddr_v4[4];        /* IPv4 destination             */
    u8   daddr_v6[16];       /* IPv6 destination             */
    char comm[TASK_COMM_LEN];
};

BPF_PERF_OUTPUT(net_events);

TRACEPOINT_PROBE(syscalls, sys_enter_connect)
{
    /*
     * args->uservaddr is a struct sockaddr __user *.
     * We only care about AF_INET and AF_INET6; skip UNIX sockets etc.
     */
    u16 family = 0;
    bpf_probe_read_user(&family, sizeof(family), args->uservaddr);

    if (family != AF_INET && family != AF_INET6)
        return 0;

    struct net_event_t ev = {};
    ev.timestamp_ns = bpf_ktime_get_ns();
    ev.pid          = bpf_get_current_pid_tgid() >> 32;
    ev.uid          = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    ev.family       = family;

    bpf_get_current_comm(&ev.comm, sizeof(ev.comm));

    if (family == AF_INET) {
        struct sockaddr_in sa4 = {};
        bpf_probe_read_user(&sa4, sizeof(sa4), args->uservaddr);
        ev.dport = ntohs(sa4.sin_port);
        bpf_probe_read(&ev.daddr_v4, sizeof(ev.daddr_v4), &sa4.sin_addr.s_addr);
    } else {
        struct sockaddr_in6 sa6 = {};
        bpf_probe_read_user(&sa6, sizeof(sa6), args->uservaddr);
        ev.dport = ntohs(sa6.sin6_port);
        bpf_probe_read(&ev.daddr_v6, sizeof(ev.daddr_v6), &sa6.sin6_addr.s6_addr);
    }

    net_events.perf_submit(args, &ev, sizeof(ev));
    return 0;
}
