#!/usr/bin/env python3
"""
PysiAdmin — ebpf/monitor.py
Standalone exec tracer. Run separately (needs root or CAP_BPF).

Install deps:   sudo dnf install bcc python3-bcc kernel-devel
Run:            sudo python3 ebpf/monitor.py
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from bcc import BPF
except ImportError:
    sys.exit(
        "[ebpf] python3-bcc not found.\n"
        "Install with: sudo dnf install bcc python3-bcc kernel-devel"
    )

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = Path("logs")
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

# ---------------------------------------------------------------------------
# BPF
# ---------------------------------------------------------------------------
PROBE_SRC = Path(__file__).parent / "probes" / "exec_monitor.c"


def handle_event(cpu, data, size):  # noqa: ARG001
    event = bpf["exec_events"].event(data)
    pid      = event.pid
    ppid     = event.ppid
    uid      = event.uid
    comm     = event.comm.decode(errors="replace")
    filename = event.filename.decode(errors="replace")
    log.info(
        "EXEC | pid=%-6d ppid=%-6d uid=%-6d comm=%-20s file=%s",
        pid, ppid, uid, comm, filename,
    )


def main() -> None:
    if os.geteuid() != 0:
        sys.exit("[ebpf] Must run as root (or with CAP_BPF + CAP_PERFMON).")

    log.info("Loading BPF program from %s", PROBE_SRC)
    global bpf
    bpf = BPF(src_file=str(PROBE_SRC))
    bpf["exec_events"].open_perf_buffer(handle_event)

    log.info("Tracing execve syscalls — Ctrl+C to stop.")
    try:
        while True:
            bpf.perf_buffer_poll()
    except KeyboardInterrupt:
        log.info("Stopped.")


if __name__ == "__main__":
    main()
