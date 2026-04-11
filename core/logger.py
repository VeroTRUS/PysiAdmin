"""
PysiAdmin — core/logger.py
Mandatory audit logging. Every command execution is recorded locally.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.settings import Settings


class AuditLogger:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._discord_bot = None  # set after bot is ready

        log_dir = Path(settings.log_dir)
        log_dir.mkdir(exist_ok=True)

        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        log_file = log_dir / f"pysi_admin_{today}.log"

        self._logger = logging.getLogger("pysi_admin.audit")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s UTC | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        self._logger.addHandler(file_handler)

        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(logging.Formatter(
            "[PysiAdmin] %(asctime)s | %(message)s",
            datefmt="%H:%M:%S",
        ))
        self._logger.addHandler(stdout_handler)

    def _write(self, domain: str, **fields) -> None:
        parts = [f"{k}={v!r}" for k, v in fields.items()]
        self._logger.info(f"{domain} | {' | '.join(parts)}")

    async def log_command(
        self,
        user_id: str,
        command: str,
        status: str,
        detail: str = "",
    ) -> None:
        self._write("CMD", user_id=user_id, cmd=command, status=status, detail=detail)

    async def log_system(self, event: str, detail: str = "") -> None:
        self._write("SYS", event=event, detail=detail)

    async def log_error(self, context: str, error: str) -> None:
        self._logger.error(f"ERR | context={context!r} | error={error!r}")
