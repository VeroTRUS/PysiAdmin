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
    # Permission tiers — add your Discord user ID (string) to owner_ids
    owner_ids:    List[str] = field(default_factory=list)
    admin_ids:    List[str] = field(default_factory=list)
    operator_ids: List[str] = field(default_factory=list)
    observer_ids: List[str] = field(default_factory=list)

    # .exec whitelist — exact commands or prefixes allowed at Admin tier
    exec_whitelist: List[str] = field(default_factory=lambda: [
        "uptime",
        "df -h",
        "free -h",
        "who",
        "w",
        "last",
        "systemctl status",
        "journalctl -n 50",
        "ip addr",
    ])

    # File transfer
    file_transfer_max_bytes: int = 52_428_800  # 50 MB

    # Optional: Discord channel ID to mirror audit logs
    log_channel_id: Optional[int] = None

    # Local log directory (gitignored via *.log)
    log_dir: str = "logs"

    @classmethod
    def load(cls) -> Settings:
        if not CONFIG_PATH.exists():
            s = cls()
            s.save()
            print(f"[PysiAdmin] Created default config at {CONFIG_PATH}")
            print("[PysiAdmin] Edit it: add your Discord user ID to owner_ids, then restart.")
            return s
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def save(self) -> None:
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.__dict__, f, indent=2)
