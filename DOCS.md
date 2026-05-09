# PysiAdmin 0.2.0 — Source Documentation

## Table of Contents
1. [Entry Point](#entry-point)
2. [config/settings.py](#configsettingspy)
3. [core/auth.py](#coreauthpy)
4. [core/crypto.py](#corecryptopy)
5. [core/logger.py](#coreloggerpy)
6. [core/parser.py](#coreparserpy)
7. [commands/system.py](#commandssystempy)
8. [commands/process.py](#commandsprocesspy)
9. [commands/files.py](#commandsfilespy)
10. [commands/exec.py](#commandsexecpy)
11. [commands/config_cmd.py](#commandsconfig_cmdpy)
12. [commands/agent.py](#commandsagentpy)
13. [ebpf/monitor.py](#ebpfmonitorpy)
14. [ebpf/probes/exec_monitor.c](#ebpfprobesexec_monitorc)
15. [ebpf/probes/net_monitor.c](#ebpfprobesnet_monitorc)
16. [native/sysinfo.c](#nativesysinfoc)
17. [native/asm_wrapper.c](#nativeasm_wrapperc)
18. [native/asm/*.S](#nativeasms)

---

## Entry Point

**`pysi_admin.py`**

Bootstraps the bot. Execution order:

1. Load `.env` via `python-dotenv`.
2. `Settings.load()` — reads or creates `pysi-config.json`.
3. `CryptoManager()` — initialises Fernet if `PYSI_ENCRYPTION_KEY` is set.
4. `build_bot()` — creates `discord.ext.commands.Bot`, attaches shared services
   (`settings`, `crypto`, `audit`, `auth`, `cmd_parser`) as bot attributes.
5. Load all command cogs from `commands/`.
6. Register `on_ready`, `on_message`, `on_command_error` event handlers.
7. `on_message` is the gatekeeper — checks `.` prefix, validates the sender
   against the user whitelist before `process_commands` is called.
8. `bot.start(token)`.

Environment variables read:
- `DISCORD_BOT_TOKEN` — required.
- `PYSI_ENCRYPTION_KEY` — optional, activates Fernet encryption.

---

## `config/settings.py`

**Class:** `Settings` (dataclass)

Persists to and loads from `pysi-config.json` (gitignored).

| Field | Type | Default | Description |
|---|---|---|---|
| `owner_ids` | `List[str]` | `[]` | Discord user IDs with full Owner access |
| `admin_ids` | `List[str]` | `[]` | Admin-tier user IDs |
| `operator_ids` | `List[str]` | `[]` | Operator-tier user IDs |
| `observer_ids` | `List[str]` | `[]` | Observer-tier user IDs (read-only) |
| `exec_mode` | `str` | `"whitelist"` | `"whitelist"` or `"denylist"` — see exec.py |
| `exec_whitelist` | `List[str]` | (large default) | Commands allowed in whitelist mode |
| `encrypt_logs` | `bool` | `false` | Encrypt audit log lines with Fernet |
| `file_transfer_max_bytes` | `int` | `52428800` | Max file size for `.file download` |
| `log_channel_id` | `int\|null` | `null` | Discord channel to mirror logs (TODO) |
| `log_dir` | `str` | `"logs"` | Local log directory |

**Methods:**
- `Settings.load()` — reads config or creates a default one on first run.
- `settings.save()` — writes current state back to JSON.

Unknown keys in the JSON file are silently ignored, ensuring forward compat.

---

## `core/auth.py`

**Enum:** `Tier(IntEnum)` — `OBSERVER=1`, `OPERATOR=2`, `ADMIN=3`, `OWNER=4`

**Class:** `AuthManager`

- `get_tier(user_id: str) → Optional[Tier]` — looks up a Discord user ID
  across all four tier lists. Returns the highest matching tier.
- `require(user_id, min_tier) → bool` — returns True if tier >= min_tier.
- `label(user_id) → str` — human-readable tier label with emoji.

**Decorator:** `require_tier(min_tier: Tier)`

A `commands.check` factory used on every command. On failure it sends a
red embed and returns `False`; the `CheckFailure` exception is swallowed in
`on_command_error`.

---

## `core/crypto.py`

**Class:** `CryptoManager`

Wraps `cryptography.fernet.Fernet`. Gracefully degrades to a passthrough if
the package is missing or the key is absent.

Key loading sequence:
1. Read `PYSI_ENCRYPTION_KEY` from environment.
2. Copy into a `bytearray`.
3. Construct `Fernet(bytes(key_buf))`.
4. Call `pysi_secure_wipe` (via ctypes → `libpysiasm.so`) to zero `key_buf`.

**Methods:**
- `encrypt(data: bytes) → bytes`
- `decrypt(data: bytes) → bytes` — raises `ValueError` on `InvalidToken`
- `encrypt_str / decrypt_str` — UTF-8 convenience wrappers
- `encrypt_file(src, dst) / decrypt_file(src, dst)` — whole-file helpers
- `CryptoManager.generate_key() → str` — static, prints a new Fernet key

**libpysiasm integration:**

`_ASM_LIB` is loaded from `native/libpysiasm.so` at module import time.
If the `.so` is absent (e.g. `make -C native` was not run), a pure-Python
fallback zeroes the bytearray with a simple loop.

---

## `core/logger.py`

**Class:** `AuditLogger`

Two handlers are always attached:
- `FileHandler` (or `_EncryptingFileHandler`) → `logs/pysi_admin_YYYYMMDD.log`
- `StreamHandler` → stdout

**`_EncryptingFileHandler`** (inner class):
Overrides `emit()` — formats the record, Fernet-encrypts the string,
writes the ciphertext token + newline directly to the file stream.
To read an encrypted log:
```python
from core.crypto import CryptoManager
cm = CryptoManager()        # needs PYSI_ENCRYPTION_KEY in env
for line in open("logs/pysi_admin_YYYYMMDD.log"):
    print(cm.decrypt_str(line.strip()))
```

**Methods:**
- `log_command(user_id, command, status, detail="")` — async, logs CMD domain
- `log_system(event, detail="")` — async, logs SYS domain
- `log_error(context, error)` — sync via `logger.error`, logs ERR domain

Log format: `YYYY-MM-DDTHH:MM:SS UTC | LEVEL | DOMAIN | key=value | ...`

---

## `core/parser.py`

**Class:** `CommandParser`

- `parse(content: str) → (command, args)` — strips the leading `.`, splits
  with `shlex.split` (handles quoted arguments correctly), returns the
  lowercase command name and a list of argument strings.
- `validate_path(path: str) → bool` — rejects empty strings and null bytes.
  TODO: per-user path restriction policy.

---

## `commands/system.py`

Observer+ tier. All commands are read-only.

| Command | Implementation |
|---|---|
| `.status` | `psutil.cpu_percent`, `virtual_memory`, `disk_usage("/")` |
| `.sysinfo` | `platform.uname`, `psutil.boot_time`, `psutil.cpu_count` |
| `.uptime` | `time.time() - psutil.boot_time()` |
| `.whoami` | Discord author info + `auth.label()` |
| `.help` | Tier-filtered command list embed |
| `.shutdown` | Owner only — calls `bot.close()` |

---

## `commands/process.py`

| Command | Tier | Implementation |
|---|---|---|
| `.ps` | Observer | `psutil.process_iter` sorted by `cpu_percent` desc, top 20 |
| `.kill <pid>` | Operator | `psutil.Process(pid).terminate()` — guards: PID 1 and agent PID refused |

---

## `commands/files.py`

| Command | Tier | Notes |
|---|---|---|
| `.file ls [path]` | Operator | Default path is `Path.home()`, **not** CWD. Max 50 entries. |
| `.file download <path>` | Operator | Uploads file to Discord channel. Capped at `file_transfer_max_bytes`. |
| `.file upload <dest>` | Admin | Reads first attachment, writes to `dest`. Refuses to overwrite. |

All paths go through `cmd_parser.validate_path()` and `Path.resolve()` before use.

---

## `commands/exec.py`

### Modes

**`whitelist`** (default):
`.exec <cmd>` is allowed only if `cmd` exactly matches or starts with an
entry in `exec_whitelist`. More predictable, harder to abuse.

**`denylist`**:
`.exec <cmd>` is allowed if:
1. No token in `BLOCKED_PATTERNS` appears in the command string.
2. The base command (first word, path-stripped) is not in `BLOCKED_COMMANDS`.

More flexible but wider surface. Recommended only for Owner-only deployments.

### Constants

`BLOCKED_PATTERNS` — sensitive file paths and env-var names. Applied to all
commands at all tiers including `.exec-raw`. Cannot be overridden at runtime.

`BLOCKED_COMMANDS` — dangerous base commands blocked in denylist mode.
Includes `rm`, `dd`, `sudo`, `bash`, `python3`, `curl`, `ssh`, etc.

### `.exec-raw`

Owner only. Skips whitelist and denylist. `BLOCKED_PATTERNS` still apply.
To unblock a pattern you must edit `exec.py` on disk — intentionally not
configurable remotely.

---

## `commands/config_cmd.py`

Admin+ tier. Reads/writes a safe subset of `pysi-config.json` remotely.

- `READABLE` — keys visible via `.config get`: exec mode, whitelist, limits.
- `WRITABLE` — keys editable via `.config set`: same minus identity/ACL keys.
  ACL fields (`owner_ids`, `*_ids`) must be edited on disk only.

Values are parsed with `json.loads` before being stored; plain strings are
accepted as fallback.

---

## `commands/agent.py`

Owner only. Manages the agent process itself.

| Command | Description |
|---|---|
| `.agent status` | PID, CPU%, RSS, uptime via `psutil.Process(os.getpid())` |
| `.agent logs [n]` | Reads last N lines of today's audit log file (max 100) |
| `.agent restart` | `bot.close()` then `os.execv(sys.executable, sys.argv)` |

---

## `ebpf/monitor.py`

Standalone process (requires root / `CAP_BPF` + `CAP_PERFMON`).
Loads two BPF programs and polls their perf buffers in a loop:

- `exec_bpf` → `exec_events` → `handle_exec()` → logs `EXEC` lines
- `net_bpf`  → `net_events`  → `handle_net()`  → logs `NET` lines

Both write to `logs/ebpf_YYYYMMDD.log` and stdout.
The loop uses `timeout=100` ms per `perf_buffer_poll` call to interleave
both buffers fairly without busy-waiting.

---

## `ebpf/probes/exec_monitor.c`

**Tracepoint:** `syscalls/sys_enter_execve`

**Rate limiting:** `BPF_HASH(rate_map, u32 pid, rate_entry_t)`.
Each PID is allowed `RATE_LIMIT_MAX` (5) events per `RATE_LIMIT_NS` (200 ms)
window. Excess events are dropped in the kernel, never sent to userspace.

**Noise filter:** Skips events where `uid==0` and `comm[0]=='('` — this
matches Linux kernel worker threads like `(sd-worker)`, `(kworker)`, etc.

**Event fields:** `timestamp_ns`, `pid`, `ppid`, `uid`, `comm[16]`, `filename[256]`

---

## `ebpf/probes/net_monitor.c`

**Tracepoint:** `syscalls/sys_enter_connect`

Only processes `AF_INET` (IPv4) and `AF_INET6` (IPv6) — skips UNIX domain
sockets and other address families.

Reads `struct sockaddr_in` or `struct sockaddr_in6` from userspace via
`bpf_probe_read_user`, extracts destination address and port.

**Event fields:** `timestamp_ns`, `pid`, `uid`, `family`, `dport`, `daddr_v4[4]` or `daddr_v6[16]`, `comm[16]`

---

## `native/sysinfo.c`

Standalone binary (`./native/sysinfo`). Outputs a JSON object to stdout:

```json
{
  "hostname": "...", "sysname": "Linux", "release": "7.x",
  "machine": "x86_64", "uptime_s": 12345,
  "total_ram_mb": 14786, "free_ram_mb": 3200,
  "load_1": 0.45, "load_5": 0.38, "load_15": 0.31,
  "procs": 342,
  "disk_total_gb": 474.35, "disk_free_gb": 302.85
}
```

Uses only POSIX/Linux syscalls: `uname(2)`, `sysinfo(2)`, `statvfs(2)`,
`gethostname(3)`. No dynamic allocation. Safe to call from untrusted contexts.

TODO: wire into `commands/system.py` as an optional subprocess backend for
`.sysinfo`, replacing the psutil path.

---

## `native/asm_wrapper.c`

C translation unit compiled together with the arch-specific `.S` file into
`libpysiasm.so`. Declares the extern asm symbols and re-exports them with
stable public names:

- `pysi_secure_wipe(void *ptr, size_t n)` → calls `pysi_secure_zero`
- `pysi_timing_now(void) → uint64_t` → calls `pysi_rdtsc` (returns 0 on
  architectures where no equivalent is available)

Loaded by `core/crypto.py` via `ctypes.CDLL`.

---

## `native/asm/*.S`

One file per supported architecture. Each provides two symbols:

### `pysi_secure_zero(void *ptr, size_t n)`

Zeroes `n` bytes starting at `ptr`. Implemented at the assembly level to
prevent the compiler from treating it as a dead store and eliding it — the
standard C `memset` optimisation is a real risk for security-critical wipes.

| Arch | Instruction used |
|---|---|
| x86\_64 | `REP STOSB` |
| arm64 | `STRB wzr, [x0], #1` loop |
| ppc64le | `STB 0, 0(r3)` loop |
| riscv64 | `SB zero, 0(a0)` loop |
| s390x | `STC r0, 0(r2)` loop |

### `pysi_rdtsc(void) → uint64_t`

Returns a high-resolution hardware counter for timing measurements.

| Arch | Register / instruction |
|---|---|
| x86\_64 | `RDTSC` (TSC) |
| arm64 | `MRS x0, cntvct_el0` (virtual counter) |
| ppc64le | `MFTB r3` (timebase) |
| riscv64 | `RDCYCLE a0` |
| s390x | `STCK` (store clock) |

All files include `.section .note.GNU-stack,"",@progbits` to mark the stack
non-executable, required for correct `NX` stack marking on Linux ELF binaries.
