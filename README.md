# PysiAdmin
### Personal System Administration Blueprint

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

> **Note:** The eBPF exec tracer (`ebpf/monitor.py`) requires Linux 4.7+ and `python3-bcc`. The rest of the agent runs on any Linux 4.x+ with Python 3.10+.

---

## Requirements

- Python 3.10 or newer
- A Discord bot token (see below)
- `git`, `gcc`, `make`
- `bcc` + `python3-bcc` + `kernel-devel` (for the eBPF tracer — optional but recommended)

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
git clone https://github.com/opfts/PysiAdmin.git
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

### Build the native sysinfo helper (optional)

```bash
make -C native
```

---

## Configuration

### 1. Bot Token

Create a `.env` file in the project root (this file is gitignored — never commit it):

```bash
echo 'DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE' > .env
```

Replace `YOUR_TOKEN_HERE` with the token you copied from the Discord Developer Portal.

### 2. `pysi-config.json`

On first run, PysiAdmin generates a default `pysi-config.json`. Edit it before starting:

```json
{
  "owner_ids":    ["YOUR_DISCORD_USER_ID"],
  "admin_ids":    [],
  "operator_ids": [],
  "observer_ids": [],
  "exec_whitelist": [
    "uptime",
    "df -h",
    "free -h",
    "ip addr",
    "systemctl status"
  ],
  "file_transfer_max_bytes": 52428800,
  "log_channel_id": null,
  "log_dir": "logs"
}
```

- `owner_ids` — your Discord user ID (string). Full control. **Add this first.**
- `admin_ids` — users who can run `.exec` (whitelist only) and `.file upload`
- `operator_ids` — users who can run `.kill`, `.file ls`, `.file download`
- `observer_ids` — users who can run read-only commands (`.status`, `.ps`, etc.)
- `exec_whitelist` — shell commands allowed via `.exec`. Add exact commands or prefixes.
- `file_transfer_max_bytes` — max file size for `.file download` (default 50 MB)
- `log_channel_id` — optional Discord channel ID to mirror audit log entries
- `log_dir` — local directory for audit logs (default `logs/`, gitignored)

---

## Permission Tiers

| Tier | Who sets it | Available commands |
|---|---|---|
| 👑 Owner | `owner_ids` in config | All commands including `.exec-raw`, `.agent`, `.shutdown` |
| ⚙️ Admin | `admin_ids` in config | `.exec <whitelisted>`, `.file upload`, `.config get/set` |
| 🔧 Operator | `operator_ids` in config | `.kill <pid>`, `.file ls`, `.file download` |
| 🔍 Observer | `observer_ids` in config | `.status`, `.sysinfo`, `.uptime`, `.whoami`, `.ps` |

Anyone not in any list is silently denied and logged.

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
| `.file ls <path>` | List a directory (Operator+) |
| `.file download <path>` | Send a file to Discord (Operator+) |
| `.file upload <dest_path>` | Save an attached file to the host (Admin+) |

### Execution (Admin+ / Owner)
| Command | Description |
|---|---|
| `.exec <command>` | Run a whitelisted shell command (Admin+) |
| `.exec-raw <command>` | Run any shell command — blocked-pattern guard still applies (Owner only) |

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

## Adding and Restricting Commands

### Adding a command to the exec whitelist

Edit `pysi-config.json` on the host machine and add to `exec_whitelist`:

```json
"exec_whitelist": [
  "uptime",
  "df -h",
  "lsblk",
  "journalctl -n 100"
]
```

Entries match exactly or as a prefix — `"journalctl -n"` allows `journalctl -n 100`, `journalctl -n 50`, etc.

Restart the agent after editing:
```
.agent restart
```

Or remotely via Discord if the agent is running:
```
.config set exec_whitelist ["uptime","df -h","lsblk","journalctl -n 100"]
```

### Restricting a command (removing from whitelist)

Remove the entry from `exec_whitelist` in `pysi-config.json` and restart.

### Permanently blocked paths and tokens

The following patterns are hardcoded in `commands/exec.py` and are **never** executable even by Owner via `.exec-raw`. To change them you must edit the source file on disk:

```
/etc/shadow       /etc/gshadow      /etc/sudoers
/root/            /proc/kcore       /dev/mem
/boot/            /sys/firmware     .ssh/id_
.env              pysi-config       DISCORD_BOT_TOKEN
```

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
[PysiAdmin] Online as PysiAdmin#1607 (ID: ...)
[PysiAdmin] Owner IDs: ['YOUR_ID_HERE']
[PysiAdmin] 12:00:00 | SYS | event='agent_start' ...
```

### Terminal 2 — eBPF exec tracer (optional, requires root)

Traces every `execve` syscall on the host and logs it to `logs/ebpf_YYYYMMDD.log`.

```bash
cd PysiAdmin
sudo .venv/bin/python3 ebpf/monitor.py
```

Expected output:
```
2026-04-11T12:00:01 UTC | Loading BPF program ...
2026-04-11T12:00:04 UTC | Tracing execve syscalls — Ctrl+C to stop.
2026-04-11T12:00:10 UTC | EXEC | pid=1234 ppid=1000 uid=1000 comm=bash file=/usr/bin/ls
```

> If `python3-bcc` is a system package (Fedora, Arch), make sure you created your venv with `--system-site-packages`.

---

## Audit Logs

All commands are logged locally regardless of outcome:

```
logs/pysi_admin_YYYYMMDD.log   ← bot command audit trail
logs/ebpf_YYYYMMDD.log         ← system-wide execve trace (if tracer is running)
```

Log files are gitignored and never leave your machine unless you explicitly send them.

---

## License

GNU General Public License v3.0 or later — see [LICENSE](LICENSE).
