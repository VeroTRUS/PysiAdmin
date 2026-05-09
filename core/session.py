"""
PysiAdmin — core/session.py
Single-use confirmation tokens for dangerous operations.

Flow:
  1. User issues a dangerous command (e.g. .exec-raw rm -rf /tmp/test)
  2. Bot stores a pending confirmation with a 30s TTL and a token
  3. Bot replies: "Confirm with: .confirm <token>"
  4. User sends .confirm <token> — bot executes the pending command
  5. Token is consumed and cannot be reused

This prevents accidental execution and adds a second-factor confirmation
step for the most sensitive commands.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class PendingConfirmation:
    token:      str
    user_id:    str
    command:    str
    callback:   Callable          # async coroutine to run on confirm
    expires_at: float = field(default_factory=lambda: time.monotonic() + 30.0)
    channel_id: Optional[int] = None


class SessionManager:
    def __init__(self) -> None:
        self._pending: Dict[str, PendingConfirmation] = {}

    def _evict_expired(self) -> None:
        now    = time.monotonic()
        stale  = [k for k, v in self._pending.items() if v.expires_at < now]
        for k in stale:
            del self._pending[k]

    def create(
        self,
        user_id:    str,
        command:    str,
        callback:   Callable,
        channel_id: Optional[int] = None,
        ttl:        int = 30,
    ) -> str:
        """
        Register a pending confirmation. Returns the 6-char hex token
        the user must supply via .confirm <token>.
        """
        self._evict_expired()
        token = secrets.token_hex(3)   # 6 hex chars, easy to type
        self._pending[token] = PendingConfirmation(
            token      = token,
            user_id    = user_id,
            command    = command,
            callback   = callback,
            expires_at = time.monotonic() + ttl,
            channel_id = channel_id,
        )
        return token

    def consume(self, token: str, user_id: str) -> Optional[PendingConfirmation]:
        """
        Validate and consume a token. Returns the PendingConfirmation
        if valid and not expired, else None.
        """
        self._evict_expired()
        entry = self._pending.get(token)
        if entry is None:
            return None
        if entry.user_id != user_id:
            return None   # wrong user
        del self._pending[token]
        return entry

    def cancel(self, user_id: str) -> int:
        """Cancel all pending confirmations for a user. Returns count removed."""
        keys = [k for k, v in self._pending.items() if v.user_id == user_id]
        for k in keys:
            del self._pending[k]
        return len(keys)
