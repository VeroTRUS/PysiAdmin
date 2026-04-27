"""
PysiAdmin — config/settings.py
Loads and saves pysi-config.json (gitignored).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

CONFIG_PATH = Path("pysi-config.json")


@dataclass
class Settings:
    # ── Identity / ACL ────────────────────────────────────────────────────────
    owner_ids:    List[str] = field(default_factory=list)
    admin_ids:    List[str] = field(default_factory=list)
    operator_ids: List[str] = field(default_factory=list)
    observer_ids: List[str] = field(default_factory=list)

    # ── Execution policy ──────────────────────────────────────────────────────
    # "whitelist" — only commands in exec_whitelist are allowed (default, safest)
    # "denylist"  — any command not matching BLOCKED_PATTERNS/BLOCKED_COMMANDS
    #               is allowed; exec_whitelist is ignored in this mode
    exec_mode: str = "whitelist"

    exec_whitelist: List[str] = field(default_factory=lambda: [
        "uptime", "date", "cal", "hostname",
        "uname -a", "uname -r",
        "whoami", "id", "pwd", "env", "printenv",
        "ls", "ls -l", "ls -la", "ls -lah",
        "stat", "file", "wc", "head", "tail",
        "cat", "less", "grep", "find", "diff",
        "md5sum", "sha256sum", "sha512sum",
        "sort", "uniq", "cut", "tr", "echo",
        "which", "whereis", "type",
        "df -h", "df -ah", "du -sh", "du -h",
        "lsblk", "lsblk -f", "blkid", "mount", "findmnt",
        "free -h", "free -m", "vmstat", "vmstat -s",
        "lscpu", "lshw", "lspci", "lsusb",
        "sensors", "numactl --hardware",
        "ps aux", "ps -ef", "pstree", "top -bn1",
        "lsof", "lsof -i",
        "ip addr", "ip route", "ip link", "ip neigh",
        "ss -tuln", "ss -tulnp",
        "netstat -tuln", "netstat -rn",
        "nmcli", "nmcli device status", "nmcli connection show",
        "ping", "ping6", "traceroute", "tracepath",
        "nslookup", "dig", "host",
        "resolvectl status", "resolvectl query",
        "curl -I", "curl -svo /dev/null",
        "systemctl status", "systemctl list-units",
        "systemctl list-units --failed", "systemctl list-timers",
        "systemctl is-active", "systemctl is-enabled",
        "journalctl -n", "journalctl -u",
        "journalctl --since", "journalctl -b", "journalctl -p err",
        "dmesg", "dmesg -T", "dmesg --level=err,warn",
        "loginctl", "loginctl list-sessions",
        "dnf list installed", "dnf list updates",
        "dnf info", "dnf check",
        "rpm -qa", "rpm -qi", "rpm -qf",
        "flatpak list", "flatpak info",
        "pip list", "pip show", "pip3 list",
        "git status", "git log", "git log --oneline",
        "git diff", "git branch", "git remote -v",
        "python3 --version", "gcc --version",
        "make --version", "cargo --version",
        "rustc --version", "node --version",
        "last", "lastlog", "who", "w",
        "groups", "getent passwd", "getent group",
        "timedatectl", "timedatectl status",
        "localectl", "hostnamectl",
        "bpftool prog list", "bpftool map list", "bpftool net list",
    ])

    # ── Security ──────────────────────────────────────────────────────────────
    # Encrypt audit log lines written to disk (requires PYSI_ENCRYPTION_KEY in .env)
    encrypt_logs: bool = False

    # ── File transfer ─────────────────────────────────────────────────────────
    file_transfer_max_bytes: int = 52_428_800  # 50 MB

    # ── Logging ───────────────────────────────────────────────────────────────
    log_channel_id: Optional[int] = None
    log_dir: str = "logs"

    # ── Class methods ─────────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> Settings:
        if not CONFIG_PATH.exists():
            s = cls()
            s.save()
            print(f"[PysiAdmin] Created default config at {CONFIG_PATH}")
            print("[PysiAdmin] Add your Discord user ID to owner_ids, then restart.")
            return s
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def save(self) -> None:
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.__dict__, f, indent=2)
