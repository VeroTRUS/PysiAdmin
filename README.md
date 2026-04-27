# PysiAdmin
### Personal System Administration Blueprint

> **Current version: 0.1.5**  
> See [CHANGELOG.md](CHANGELOG.md) for what changed. See [DOCS.md](DOCS.md) for full source documentation.

## What is PysiAdmin?
PysiAdmin is a transparent, remote administration agent designed for personal infrastructure management via a Discord-based Command & Control (C2) interface.

Originally derived from the Pysilon codebase, PysiAdmin has been ***completely gutted*** of all malicious telemetry, surveillance modules, and stealth-persistence mechanisms. It has been refactored into a legitimate, auditable tool for systems administrators who require remote access to their own machines without the overhead of heavy enterprise suites.

---

## Platform Support

| Platform | Status |
|---|---|
| Linux Kernel 4.x – 7.x | ✅ Supported |
| OpenBSD / FreeBSD / NetBSD | 🔜 Planned — 0.2.0 |
| OpenIndiana (illumos) | 🔜 Planned — 0.3.0 |

**CPU architectures:** x86\_64 (AMD64 & Intel64), ARM64, IBM PowerPC, RISC-V, IBM s390x

> **Note:** The eBPF tracers (`ebpf/monitor.py`) require Linux 4.7+ and `python3-bcc`. The rest of the agent runs on any Linux 4.x+ with Python 3.10+.

---

## Requirements

- Python 3.10 or newer
- A Discord bot token (see below)
- `git`, `gcc`, `make`
- `cryptography` Python package (installed via `requirements.txt`)
- `bcc` + `python3-bcc` + `kernel-devel` — for the eBPF tracer (optional but recommended)

---

## Discord Developer Portal Setup

Before installing, you need a bot token.

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** — name it `PysiAdmin` (or anything you like)
3. Go to the **Bot** tab:
   - Click **Reset Token** → copy the token somewhere safe
   - Enable **Message Content Intent** → **ON** ← required, the bot cannot read commands without this
   - Leave **Server Members Intent** and **Presence Intent** OFF
4. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Messages / View Channels`, `Attach Files`, `Embed Links`
   - Copy the generated URL, open it in your browser, and invite the bot to your **private server**

---

## Finding Your Discord User ID

You need your own Discord user ID to set yourself as Owner.

1. Open Discord → **Settings** → **Advanced** → enable **Developer Mode**
2. Right-click your own username anywhere → **Copy User ID**

---

## Installation

### Fedora / RHEL / CentOS

```bash
sudo dnf install git gcc make python3 python3-pip bcc python3-bcc kernel-devel
```

### Debian / Ubuntu / Linux Mint

```bash
sudo apt update
sudo apt install git gcc make python3 python3-pip python3-venv bpfcc-tools python3-bpfcc linux-headers-$(uname -r)
```

### Arch Linux / Manjaro / ArcoLinux

```bash
sudo pacman -S git gcc make python python-pip bcc bcc-tools python-bcc linux-headers
```

### Gentoo

```bash
sudo emerge --ask dev-vcs/git sys-devel/gcc sys-devel/make dev-lang/python dev-util/bcc
```

### Slackware

```bash
# Install python3, gcc, make via slackpkg or source
# BCC must be built from source: https://github.com/iovisor/bcc/blob/master/INSTALL.md
slackpkg install python3 gcc make kernel-headers
```

### Solus

```bash
sudo eopkg install git gcc make python3 python3-pip kernel-headers
# BCC must be built from source on Solus
```

### LFS (Linux From Scratch)

Install `python3`, `gcc`, `make`, and `kernel-headers` per your LFS book.  
BCC must be built from source: https://github.com/iovisor/bcc/blob/master/INSTALL.md

---

## Clone and Set Up

```bash
git clone https://github.com/VeroTRUS/PysiAdmin.git
cd PysiAdmin
```

### Create the virtual environment

```bash
# Standard (no system packages):
python3 -m venv .venv

# If your distro's python3-bcc is system-only (Fedora, Arch, etc.),
# allow the venv to see it:
python3 -m venv --system-site-packages .venv
```

### Activate and install dependencies

```bash
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Build the native helpers

Builds `native/sysinfo` (JSON system info binary) and `native/libpysiasm.so`
(arch-specific assembly for secure memory wiping). Architecture is detected
automatically — x86\_64, ARM64, ppc64le, riscv64, and s390x are supported.

```bash
make -C native
```

---

## Configuration

### 1. Bot Token

Create a `.env` file in the project root (gitignored — never commit it):

```bash
echo 'DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE' > .env
```

Replace `YOUR_TOKEN_HERE` with the token from the Discord Developer Portal.

#### Optional — Audit log encryption

Generate a Fernet key and add it to `.env` to encrypt log lines written to disk:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the output to `.env`:

```bash
echo 'PYSI_ENCRYPTION_KEY=YOUR_GENERATED_KEY_HERE' >> .env
```

Then enable it in `pysi-config.json`:

```json
"encrypt_logs": true
```

### 2. `pysi-config.json`

On first run, PysiAdmin generates a default `pysi-config.json`. Edit it before starting:

```json
{
  "owner_ids":    ["YOUR_DISCORD_USER_ID"],
  "admin_ids":    [],
  "operator_ids": [],
  "observer_ids": [],
  "exec_mode":    "whitelist",
  "exec_whitelist": [
    "uptime",
    "df -h",
    "free -h",
    "ip addr",
    "systemctl status"
  ],
  "encrypt_logs": false,
  "file_transfer_max_bytes": 52428800,
  "log_channel_id": null,
  "log_dir": "logs"
}
```

| Field | Description |
|---|---|
| `owner_ids` | Your Discord user ID (string). Full control. **Add this first.** |
| `admin_ids` | Users who can run `.exec` and `.file upload` |
| `operator_ids` | Users who can run `.kill`, `.file ls`, `.file download` |
| `observer_ids` | Users who can run read-only commands |
| `exec_mode` | `"whitelist"` (safest, default) or `"denylist"` (more freedom — see below) |
| `exec_whitelist` | Commands allowed via `.exec` in whitelist mode |
| `encrypt_logs` | Encrypt audit log lines on disk with Fernet (requires `PYSI_ENCRYPTION_KEY`) |
| `file_transfer_max_bytes` | Max file size for `.file download` (default 50 MB) |
| `log_channel_id` | Optional Discord channel ID to mirror audit log entries |
| `log_dir` | Local log directory (default `logs/`, gitignored) |

---

## Permission Tiers

| Tier | Who sets it | Available commands |
|---|---|---|
| 👑 Owner | `owner_ids` | All commands including `.exec-raw`, `.agent`, `.shutdown` |
| ⚙️ Admin | `admin_ids` | `.exec`, `.file upload`, `.config get/set` |
| 🔧 Operator | `operator_ids` | `.kill <pid>`, `.file ls`, `.file download` |
| 🔍 Observer | `observer_ids` | `.status`, `.sysinfo`, `.uptime`, `.whoami`, `.ps` |

Anyone not in any list is denied and logged.

---

## Command Reference

### System (Observer+)
| Command | Description |
|---|---|
| `.status` | CPU / RAM / Disk snapshot |
| `.sysinfo` | Hostname, OS, kernel, arch, uptime |
| `.uptime` | System uptime |
| `.whoami` | Your Discord ID and current tier |
| `.help` | Show commands available at your tier |

### Process (Observer+ / Operator+)
| Command | Description |
|---|---|
| `.ps` | Top 20 processes by CPU usage |
| `.kill <pid>` | Send SIGTERM to a process (Operator+) |

### Files (Operator+ / Admin+)
| Command | Description |
|---|---|
| `.file ls [path]` | List a directory — defaults to home dir (Operator+) |
| `.file download <path>` | Send a file to Discord (Operator+) |
| `.file upload <dest_path>` | Save an attached file to the host (Admin+) |

### Execution (Admin+ / Owner)
| Command | Description |
|---|---|
| `.exec <command>` | Run a shell command — whitelist or denylist mode (Admin+) |
| `.exec-raw <command>` | Run any command — `BLOCKED_PATTERNS` still apply (Owner only) |

### Config (Admin+)
| Command | Description |
|---|---|
| `.config get <key>` | Read a config value |
| `.config set <key> <value>` | Update and save a config value |

### Agent (Owner)
| Command | Description |
|---|---|
| `.agent status` | Memory / CPU / uptime of the agent process |
| `.agent logs [n]` | Tail last N lines of today's audit log (default 50) |
| `.agent restart` | Graceful restart via os.execv |
| `.shutdown` | Disconnect and stop the agent |

---

## Execution Modes

### `whitelist` (default, safest)

`.exec` only runs commands listed in `exec_whitelist`. Anything not listed is denied.

```json
"exec_mode": "whitelist"
```

### `denylist` (more freedom)

`.exec` runs any command that does not match `BLOCKED_PATTERNS` or
`BLOCKED_COMMANDS` (hardcoded in `commands/exec.py`). The `exec_whitelist`
field is ignored in this mode.

```json
"exec_mode": "denylist"
```

Permanently blocked in denylist mode (not configurable remotely):
`rm`, `dd`, `sudo`, `bash`, `python3`, `curl`, `wget`, `ssh`, `nc`, `strace`,
`kill`, `reboot`, `modprobe`, `docker`, and more — see `BLOCKED_COMMANDS`
in `commands/exec.py` for the full list.

### Always blocked (all modes, all tiers, including `.exec-raw`)

These patterns are hardcoded and can only be changed by editing `commands/exec.py` on disk:

```
/etc/shadow       /etc/gshadow      /etc/sudoers
/root/            /proc/kcore       /dev/mem
/boot/            /sys/firmware     .ssh/id_
.env              pysi-config       DISCORD_BOT_TOKEN
```

---

## Adding and Restricting Commands

### Adding a command to the exec whitelist

Edit `pysi-config.json` and add to `exec_whitelist`:

```json
"exec_whitelist": [
  "uptime",
  "df -h",
  "lsblk",
  "journalctl -n 100"
]
```

Entries match exactly or as a prefix — `"journalctl -n"` allows
`journalctl -n 100`, `journalctl -n 50`, etc.

Apply without restarting the bot:

```
.config set exec_whitelist ["uptime","df -h","lsblk","journalctl -n 100"]
```

Or restart after editing the file on disk:

```
.agent restart
```

### Restricting a command

Remove the entry from `exec_whitelist` and restart, or switch back to
`whitelist` mode if you were using `denylist`.

---

## Running PysiAdmin

### Terminal 1 — The agent

```bash
cd PysiAdmin
source .venv/bin/activate
python3 pysi_admin.py
```

Expected output:

```
[crypto] Encryption enabled (Fernet / AES-128-CBC + HMAC-SHA256).   <- if key is set
[PysiAdmin] Online as PysiAdmin#1607 (ID: ...)
[PysiAdmin] Owner IDs: ['YOUR_ID_HERE']
[PysiAdmin] Exec mode: whitelist
[PysiAdmin] 12:00:00 | SYS | event='agent_start' ...
```

### Terminal 2 — eBPF tracers (optional, requires root)

Traces every `execve` and outbound TCP/UDP `connect` syscall on the host.
Logs to `logs/ebpf_YYYYMMDD.log`.

```bash
cd PysiAdmin
sudo .venv/bin/python3 ebpf/monitor.py
```

Expected output:

```
2026-04-26T12:00:01 UTC | Loading exec probe from ebpf/probes/exec_monitor.c
2026-04-26T12:00:02 UTC | Loading net probe from ebpf/probes/net_monitor.c
2026-04-26T12:00:03 UTC | Tracing execve + connect syscalls -- Ctrl+C to stop.
2026-04-26T12:00:10 UTC | EXEC | ts_ms=... pid=1234 ppid=1000 uid=1000 comm=bash                 file=/usr/bin/ls
2026-04-26T12:00:11 UTC | NET  | pid=1234 uid=1000 comm=curl                 dst=93.184.216.34:443
```

> If `python3-bcc` is a system package (Fedora, Arch), make sure you created
> your venv with `--system-site-packages`.

---

## Audit Logs

All commands are logged locally regardless of outcome:

```
logs/pysi_admin_YYYYMMDD.log   <- bot command audit trail (optionally encrypted)
logs/ebpf_YYYYMMDD.log         <- execve + connect trace (if tracer is running)
```

Log files are gitignored and never leave your machine unless you explicitly send them.

To read an encrypted audit log:

```python
from dotenv import load_dotenv
from core.crypto import CryptoManager
load_dotenv()
cm = CryptoManager()
for line in open("logs/pysi_admin_YYYYMMDD.log"):
    print(cm.decrypt_str(line.strip()))
```

---

## License

GNU General Public License v3.0 or later — see [LICENSE](LICENSE).
