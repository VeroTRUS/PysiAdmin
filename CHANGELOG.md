# Changelog

## [0.2.0] — 2026-05-09

### Added
- **BSD support** — FreeBSD, OpenBSD, NetBSD fully supported.
  - `compat/platform.py` — runtime OS detection, platform-specific whitelist additions,
    package manager detection, `IS_LINUX` / `IS_BSD` / `IS_FREEBSD` etc. flags.
  - `dtrace/` — four DTrace scripts replacing eBPF on BSD:
    `exec_monitor.d`, `net_monitor.d`, `file_monitor.d`, `priv_monitor.d`, `monitor.sh`.
  - `install.sh` — rewritten as POSIX sh, auto-detects Linux distro or BSD variant,
    uses `gmake` on BSD, `dtrace` instructions on BSD.
- **VeroCC support** — `native/Makefile` now detects `vcc` (VeroCC) and uses it
  as the compiler when available, falling back to `gcc` otherwise.
- **Two new eBPF probes** (Linux only):
  - `ebpf/probes/file_monitor.c` — traces `openat(2)` calls on sensitive paths
    (`/etc/`, `/root/`, `/boot/`, `/proc/`, `/sys/`).
  - `ebpf/probes/priv_monitor.c` — alerts on `setresuid(0)` / `setresgid(0)`
    privilege escalation attempts.
- **`core/ratelimit.py`** — sliding-window per-user rate limiter. Configurable via
  `rate_limit_commands` and `rate_limit_window` in `pysi-config.json`. Owners exempt.
- **`core/session.py`** — single-use confirmation tokens for `.exec-raw`.
  When `confirm_exec_raw: true` (default), the Owner must type `.confirm <token>`
  within 30 seconds to execute. `.cancel` aborts all pending confirmations.
- **`compat/`** package — `platform.py` with BSD-specific exec whitelist entries
  and OS label detection.
- **Channel restriction** — new `allowed_channel_ids` config field. When non-empty,
  the bot only processes commands from those Discord channel IDs.
- **Assembly v2** — all five arch `.S` files (`x86_64`, `arm64`, `ppc64le`,
  `riscv64`, `s390x`) now export two new symbols:
  - `pysi_ct_compare` — constant-time byte comparison (no timing side-channel).
  - `pysi_stack_guard` — software stack canary check helper.
- **`native/asm_wrapper.c`** updated — exports `pysi_ct_memcmp` and `pysi_check_stack`.
- **`pysi_admin.py`** startup now prints platform label, eBPF availability,
  exec mode, and rate-limit config on boot.

### Changed
- Platform support table in README updated: BSD is now ✅ Supported, OpenIndiana
  remains 🔜 Planned — 0.3.0.
- `config/settings.py` — new fields: `confirm_exec_raw`, `rate_limit_commands`,
  `rate_limit_window`, `allowed_channel_ids`.
- `commands/exec.py` — BSD-specific sensitive paths added to `BLOCKED_PATTERNS`;
  BSD tools (`jail`, `kldload`, `kldunload`, `truss`, `kdump`, `csh`, `tcsh`)
  added to `BLOCKED_COMMANDS`. `.confirm` and `.cancel` commands added.
- `ebpf/monitor.py` — now loads four probes instead of two.

## [0.1.5] — 2026-04-26

### Added
- `core/crypto.py` — Fernet (AES-128-CBC + HMAC-SHA256) encryption for audit logs.
- `native/asm/` — arch-specific assembly for `pysi_secure_zero` and `pysi_rdtsc`.
- `native/libpysiasm.so` — shared library loaded via ctypes for secure memory wipe.
- `ebpf/probes/net_monitor.c` — connect(2) tracing (IPv4 + IPv6).
- `exec_mode` config — `"whitelist"` (default) or `"denylist"`.
- `DOCS.md` — inline source documentation.

### Fixed
- `.file ls` default path was agent CWD (exposed project directory). Now defaults to `~`.

### Changed
- eBPF exec probe: rate limiting + kernel thread noise filter.
- `requirements.txt`: added `cryptography>=42.0.0`.

## [0.1.0] — 2026-04-11

- Initial release. Discord C2 agent with tier-based auth, whitelist exec,
  file transfer, process management, and eBPF exec tracer.
