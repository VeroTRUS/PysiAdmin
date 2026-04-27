"""
PysiAdmin — core/logger.py
Mandatory audit logging. Every command is recorded locally.
If encrypt_logs=true in config and PYSI_ENCRYPTION_KEY is set,
each log line is Fernet-encrypted before being written to disk.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from config.settings import Settings

if TYPE_CHECKING:
    from core.crypto import CryptoManager


class _EncryptingFileHandler(logging.FileHandler):
    """FileHandler that optionally Fernet-encrypts each log record."""

    def __init__(self, path: str, crypto: "CryptoManager") -> None:
        super().__init__(path)
        self._crypto = crypto

    def emit(self, record: logging.LogRecord) -> None:
        if not self._crypto.enabled:
            super().emit(record)
            return
        try:
            msg      = self.format(record)
            enc      = self._crypto.encrypt_str(msg)
            stream   = self.stream
            stream.write(enc + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class AuditLogger:
    def __init__(self, settings: Settings, crypto: "CryptoManager") -> None:
        self.settings = settings
        self.crypto   = crypto

        log_dir = Path(settings.log_dir)
        log_dir.mkdir(exist_ok=True)

        today    = datetime.now(timezone.utc).strftime("%Y%m%d")
        log_file = log_dir / f"pysi_admin_{today}.log"

        self._logger = logging.getLogger("pysi_admin.audit")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        if settings.encrypt_logs and crypto.enabled:
            file_handler = _EncryptingFileHandler(str(log_file), crypto)
            print("[logger] Audit log encryption: ON")
        else:
            file_handler = logging.FileHandler(str(log_file))

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
