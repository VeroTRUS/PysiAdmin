"""
PysiAdmin — core/ratelimit.py
Sliding-window per-user rate limiter for Discord commands.
Configured via pysi-config.json:
  rate_limit_commands: int  — max commands per window (default 15)
  rate_limit_window:   int  — window size in seconds (default 60)
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict


class RateLimiter:
    def __init__(self, max_commands: int = 15, window_seconds: int = 60) -> None:
        self.max_commands   = max_commands
        self.window_seconds = window_seconds
        # user_id -> deque of timestamps of recent commands
        self._windows: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, user_id: str) -> tuple[bool, int]:
        """
        Returns (allowed: bool, retry_after: int).
        retry_after is the number of seconds until the user can send again.
        Allowed is True if the command should proceed.
        """
        now    = time.monotonic()
        cutoff = now - self.window_seconds
        dq     = self._windows[user_id]

        # Evict timestamps outside the current window
        while dq and dq[0] < cutoff:
            dq.popleft()

        if len(dq) >= self.max_commands:
            # Oldest timestamp in window + window_seconds = when first slot frees
            retry_after = int(dq[0] + self.window_seconds - now) + 1
            return False, retry_after

        dq.append(now)
        return True, 0

    def reset(self, user_id: str) -> None:
        """Clear rate limit state for a user (Owner can use this)."""
        self._windows.pop(user_id, None)
