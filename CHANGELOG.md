# Changelog

## [0.1.5] — 2026-04-27

### Added
- `core/crypto.py` — Fernet (AES-128-CBC + HMAC-SHA256) encryption for audit
  log lines and file payloads. Activated via `PYSI_ENCRYPTION_KEY` in `.env`
  and `encrypt_logs: true` in `pysi-config.json`.
- `native/asm/` — Architecture-specific assembly (`x86_64`, `arm64`, `ppc64le`,
  `riscv64`, `s390x`) providing `pysi_secure_zero` and `pysi_rdtsc`. Built into
  `native/libpysiasm.so` and used by `CryptoManager` to wipe key material from
  memory after use.
- `native/asm_wrapper.c` — C shim exposing `pysi_secure_wipe` and
  `pysi_timing_now` as shared-library symbols loaded via ctypes.
- `ebpf/probes/net_monitor.c` — New eBPF tracepoint for `sys_enter_connect`.
  Logs outbound TCP/UDP connections (IPv4 + IPv6) with PID, UID, comm, and
  destination address/port.
- `exec_mode` config option — `"whitelist"` (default) or `"denylist"`.
  Denylist mode allows any command not matching `BLOCKED_PATTERNS` or
  `BLOCKED_COMMANDS`, without requiring it to appear in `exec_whitelist`.
- `DOCS.md` — Inline documentation for every source file and module.

### Fixed
- `.file ls` with no argument defaulted to the agent's working directory
  (the PysiAdmin project folder), exposing the project structure. It now
  defaults to the home directory of the user running the agent.

### Changed
- eBPF exec probe now rate-limits noisy PIDs (max 5 events per 200 ms per PID)
  and filters kernel worker threads, eliminating the bwrap/gly-hdl flooding
  seen at startup.
- `ebpf/monitor.py` now polls both `exec_events` and `net_events` buffers.
- "Tested on Fedora 45 Linux 7.0rc\*" simplified to "Tested on Fedora Rawhide".
- `native/Makefile` auto-detects host architecture and builds `libpysiasm.so`
  only when a matching `.S` file exists.
- `requirements.txt` — added `cryptography>=42.0.0`.

## [0.1.0] — 2026-04-11

- Initial release. Discord C2 agent with tier-based auth, whitelist exec,
  file transfer, process management, and eBPF exec tracer.

