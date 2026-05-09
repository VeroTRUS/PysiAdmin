"""
PysiAdmin — config/settings.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

CONFIG_PATH = Path("pysi-config.json")


@dataclass
class Settings:
    # ── ACL ───────────────────────────────────────────────────────────────────
    owner_ids:    List[str] = field(default_factory=list)
    admin_ids:    List[str] = field(default_factory=list)
    operator_ids: List[str] = field(default_factory=list)
    observer_ids: List[str] = field(default_factory=list)

    # ── Execution ─────────────────────────────────────────────────────────────
    exec_mode: str = "whitelist"   # "whitelist" | "denylist"
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
        "lscpu", "lshw", "lspci", "lsusb", "sensors",
        "ps aux", "ps -ef", "pstree", "top -bn1",
        "lsof", "lsof -i",
        "ip addr", "ip route", "ip link", "ip neigh",
        "ss -tuln", "ss -tulnp",
        "netstat -tuln", "netstat -rn",
        "nmcli", "nmcli device status",
        "ping", "ping6", "traceroute", "tracepath",
        "nslookup", "dig", "host", "resolvectl status",
        "curl -I", "curl -svo /dev/null",
        "systemctl status", "systemctl list-units",
        "systemctl list-units --failed", "systemctl list-timers",
        "systemctl is-active", "systemctl is-enabled",
        "journalctl -n", "journalctl -u",
        "journalctl --since", "journalctl -b", "journalctl -p err",
        "dmesg", "dmesg -T",
        "loginctl", "loginctl list-sessions",
        "dnf list installed", "dnf list updates", "dnf info",
        "rpm -qa", "rpm -qi", "rpm -qf",
        "apt list --installed", "apt show",
        "flatpak list", "pip list", "pip show",
        "git status", "git log", "git log --oneline",
        "git diff", "git branch", "git remote -v",
        "python3 --version", "gcc --version",
        "vcc --version",          # VeroCC
        "make --version", "cargo --version",
        "rustc --version", "node --version",
        "last", "lastlog", "who", "w",
        "groups", "getent passwd", "getent group",
        "timedatectl", "timedatectl status",
        "localectl", "hostnamectl",
        "bpftool prog list", "bpftool map list",
        # BSD
        "ifconfig", "ifconfig -a",
        "sockstat", "sockstat -l",
        "fstat", "sysctl", "sysctl -a",
        "service -e", "service -l",
        "rcctl ls all", "rcctl ls started",
        "pkg info", "pkg_info", "pkgin list",
        "pfctl -s rules", "pfctl -s info",
        "gpart show",
    ])

    # ── Security ──────────────────────────────────────────────────────────────
    encrypt_logs:     bool      = False
    # Require .confirm <token> before running .exec-raw (Owner only)
    confirm_exec_raw: bool      = True
    # Rate limiting
    rate_limit_commands: int    = 15     # max commands per window
    rate_limit_window:   int    = 60     # window size in seconds
    # Restrict commands to specific channel IDs (empty = any channel)
    allowed_channel_ids: List[int] = field(default_factory=list)

    # ── File transfer ─────────────────────────────────────────────────────────
    file_transfer_max_bytes: int = 52_428_800

    # ── Logging ───────────────────────────────────────────────────────────────
    log_channel_id: Optional[int] = None
    log_dir:        str           = "logs"

    @classmethod
    def load(cls) -> Settings:
        if not CONFIG_PATH.exists():
            s = cls()
            s.save()
            print(f"[PysiAdmin] Created default config at {CONFIG_PATH}")
            return s
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def save(self) -> None:
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.__dict__, f, indent=2)
