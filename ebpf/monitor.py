#!/usr/bin/env python3
"""
PysiAdmin — ebpf/monitor.py
Loads exec_monitor.c and net_monitor.c via python3-bcc.
Logs all events to logs/ebpf_YYYYMMDD.log.

Run: sudo .venv/bin/python3 ebpf/monitor.py
"""

from __future__ import annotations

import logging
import os
import socket
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from bcc import BPF
except ImportError:
    sys.exit(
        "[ebpf] python3-bcc not found.\n"
        "Install: sudo dnf install bcc python3-bcc kernel-devel\n"
        "Then rebuild venv: python3 -m venv --system-site-packages .venv"
    )

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_DIR  = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
_today   = datetime.now(timezone.utc).strftime("%Y%m%d")
_logfile = LOG_DIR / f"ebpf_{_today}.log"

logging.basicConfig(
    handlers=[
        logging.FileHandler(_logfile),
        logging.StreamHandler(sys.stdout),
    ],
    level=logging.INFO,
    format="%(asctime)s UTC | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("pysi_admin.ebpf")

# ── Probe paths ───────────────────────────────────────────────────────────────
_PROBE_DIR  = Path(__file__).parent / "probes"
EXEC_PROBE  = _PROBE_DIR / "exec_monitor.c"
NET_PROBE   = _PROBE_DIR / "net_monitor.c"


# ── Event handlers ────────────────────────────────────────────────────────────

def handle_exec(cpu, data, size):  # noqa: ARG001
    ev       = exec_bpf["exec_events"].event(data)
    pid      = ev.pid
    ppid     = ev.ppid
    uid      = ev.uid
    comm     = ev.comm.decode(errors="replace")
    filename = ev.filename.decode(errors="replace")
    ts_ms    = ev.timestamp_ns // 1_000_000
    log.info(
        "EXEC | ts_ms=%-14d pid=%-6d ppid=%-6d uid=%-6d comm=%-20s file=%s",
        ts_ms, pid, ppid, uid, comm, filename,
    )


def handle_net(cpu, data, size):  # noqa: ARG001
    ev   = net_bpf["net_events"].event(data)
    pid  = ev.pid
    uid  = ev.uid
    comm = ev.comm.decode(errors="replace")
    port = ev.dport

    if ev.family == 2:   # AF_INET
        addr = socket.inet_ntop(socket.AF_INET, bytes(ev.daddr_v4))
    else:                # AF_INET6
        addr = socket.inet_ntop(socket.AF_INET6, bytes(ev.daddr_v6))

    log.info(
        "NET  | pid=%-6d uid=%-6d comm=%-20s dst=%s:%d",
        pid, uid, comm, addr, port,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if os.geteuid() != 0:
        sys.exit("[ebpf] Must run as root (or with CAP_BPF + CAP_PERFMON).")

    global exec_bpf, net_bpf

    log.info("Loading exec probe from %s", EXEC_PROBE)
    exec_bpf = BPF(src_file=str(EXEC_PROBE))
    exec_bpf["exec_events"].open_perf_buffer(handle_exec)

    log.info("Loading net probe from %s", NET_PROBE)
    net_bpf = BPF(src_file=str(NET_PROBE))
    net_bpf["net_events"].open_perf_buffer(handle_net)

    log.info("Tracing execve + connect syscalls — Ctrl+C to stop.")
    try:
        while True:
            exec_bpf.perf_buffer_poll(timeout=100)
            net_bpf.perf_buffer_poll(timeout=100)
    except KeyboardInterrupt:
        log.info("Stopped.")


if __name__ == "__main__":
    main()
