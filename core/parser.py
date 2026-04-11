"""
PysiAdmin — core/parser.py
Safe command parsing using shlex. No arbitrary text execution.
"""

from __future__ import annotations

import shlex
from typing import List, Tuple

from config.settings import Settings


class ParseError(Exception):
    pass


class CommandParser:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def parse(self, content: str) -> Tuple[str, List[str]]:
        """Parse '.command [args...]' safely."""
        if not content.startswith("."):
            raise ParseError("Not a command")
        try:
            parts = shlex.split(content[1:])
        except ValueError as exc:
            raise ParseError(f"Bad syntax: {exc}") from exc
        if not parts:
            raise ParseError("Empty command")
        return parts[0].lower(), parts[1:]

    def validate_path(self, path: str) -> bool:
        """Reject obviously dangerous paths."""
        if not path or "\x00" in path:
            return False
        # TODO: add per-user path restriction policy if desired
        return True
