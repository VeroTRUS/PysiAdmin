#!/usr/bin/env python3
"""
PysiAdmin — ebpf/monitor.py  (0.2.0)
Loads all four Linux eBPF probes:
  exec_monitor   — execve(2) tracing
  net_monitor    — connect(2) tracing
  file_monitor   — openat(2) on sensitive paths
  priv_monitor   — setresuid/setresgid root escalation attempts

BSD users: run dtrace/monitor.sh instead.
Run: sudo .venv/bin/python3 ebpf/monitor.py
"""

from __future__ import annotations

import logging
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from bcc import BPF
except ImportError:
    sys.exit(
        "[ebpf] python3-bcc not found.\n"
        "Linux install: sudo dnf install bcc python3-bcc kernel-devel\n"
        "BSD users: run dtrace/monitor.sh instead."
    )

LOG_DIR  = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
_today   = datetime.now(timezone.utc).strftime("%Y%m%d")
_logfile = LOG_DIR / f"ebpf_{_today}.log"

logging.basicConfig(
    handlers=[logging.FileHandler(_logfile), logging.StreamHandler(sys.stdout)],
    level=logging.INFO,
    format="%(asctime)s UTC | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("pysi_admin.ebpf")

_PROBE_DIR   = Path(__file__).parent / "probes"
EXEC_PROBE   = _PROBE_DIR / "exec_monitor.c"
NET_PROBE    = _PROBE_DIR / "net_monitor.c"
FILE_PROBE   = _PROBE_DIR / "file_monitor.c"
PRIV_PROBE   = _PROBE_DIR / "priv_monitor.c"


def handle_exec(cpu, data, size):
    ev = exec_bpf["exec_events"].event(data)
    log.info("EXEC  | pid=%-6d ppid=%-6d uid=%-6d comm=%-20s file=%s",
             ev.pid, ev.ppid, ev.uid,
             ev.comm.decode(errors="replace"),
             ev.filename.decode(errors="replace"))

def handle_net(cpu, data, size):
    ev   = net_bpf["net_events"].event(data)
    addr = (socket.inet_ntop(socket.AF_INET,  bytes(ev.daddr_v4))
            if ev.family == 2
            else socket.inet_ntop(socket.AF_INET6, bytes(ev.daddr_v6)))
    log.info("NET   | pid=%-6d uid=%-6d comm=%-20s dst=%s:%d",
             ev.pid, ev.uid, ev.comm.decode(errors="replace"), addr, ev.dport)

def handle_file(cpu, data, size):
    ev = file_bpf["file_events"].event(data)
    log.warning("FILE  | pid=%-6d uid=%-6d flags=0x%04x comm=%-20s path=%s",
                ev.pid, ev.uid, ev.flags,
                ev.comm.decode(errors="replace"),
                ev.filename.decode(errors="replace"))

def handle_priv(cpu, data, size):
    ev   = priv_bpf["priv_events"].event(data)
    kind = "SETRESGID" if ev.is_gid else "SETRESUID"
    log.warning("PRIV  | ⚠️  %s | pid=%-6d current_uid=%-6d target=%d/%d/%d comm=%s",
                kind, ev.pid, ev.current_uid,
                ev.target_ruid, ev.target_euid, ev.target_suid,
                ev.comm.decode(errors="replace"))


def main() -> None:
    if os.geteuid() != 0:
        sys.exit("[ebpf] Must run as root (or CAP_BPF + CAP_PERFMON).")

    global exec_bpf, net_bpf, file_bpf, priv_bpf

    for probe, var_name, label in [
        (EXEC_PROBE,  "exec_bpf",  "exec"),
        (NET_PROBE,   "net_bpf",   "net"),
        (FILE_PROBE,  "file_bpf",  "file"),
        (PRIV_PROBE,  "priv_bpf",  "priv"),
    ]:
        log.info("Loading %s probe from %s", label, probe)
        globals()[var_name] = BPF(src_file=str(probe))

    exec_bpf["exec_events"].open_perf_buffer(handle_exec)
    net_bpf["net_events"].open_perf_buffer(handle_net)
    file_bpf["file_events"].open_perf_buffer(handle_file)
    priv_bpf["priv_events"].open_perf_buffer(handle_priv)

    log.info("Tracing execve + connect + openat(sensitive) + setresuid — Ctrl+C to stop.")
    try:
        while True:
            for b in (exec_bpf, net_bpf, file_bpf, priv_bpf):
                b.perf_buffer_poll(timeout=50)
    except KeyboardInterrupt:
        log.info("Stopped.")

if __name__ == "__main__":
    main()
