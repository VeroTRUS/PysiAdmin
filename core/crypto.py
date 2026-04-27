"""
PysiAdmin — core/crypto.py
Symmetric encryption via Fernet (AES-128-CBC + HMAC-SHA256).
Wrapped through arch-specific secure_wipe via ctypes when libpysiasm.so
is available, so key material is reliably zeroed after use.

To generate a key:
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Add to .env:
    PYSI_ENCRYPTION_KEY=<output above>
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
from typing import Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False

# Try to load the native secure-wipe library built by native/Makefile
_ASM_LIB: Optional[ctypes.CDLL] = None
_LIB_PATH = Path(__file__).parent.parent / "native" / "libpysiasm.so"
if _LIB_PATH.exists():
    try:
        _ASM_LIB = ctypes.CDLL(str(_LIB_PATH))
        _ASM_LIB.pysi_secure_wipe.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        _ASM_LIB.pysi_secure_wipe.restype  = None
    except OSError:
        _ASM_LIB = None


def _secure_wipe_bytes(buf: bytearray) -> None:
    """Zero a bytearray in-place using the ASM routine when available."""
    if _ASM_LIB is not None and len(buf) > 0:
        addr = (ctypes.c_char * len(buf)).from_buffer(buf)
        _ASM_LIB.pysi_secure_wipe(addr, len(buf))
    else:
        for i in range(len(buf)):
            buf[i] = 0


class CryptoManager:
    """
    Manages optional Fernet encryption for audit log lines and file payloads.
    If PYSI_ENCRYPTION_KEY is absent or cryptography is not installed,
    all methods pass data through unchanged.
    """

    def __init__(self) -> None:
        self._fernet: Optional[Fernet] = None
        self._enabled = False

        if not _CRYPTO_OK:
            print("[crypto] 'cryptography' not installed — encryption disabled.")
            return

        raw_key = os.getenv("PYSI_ENCRYPTION_KEY", "")
        if not raw_key:
            print("[crypto] PYSI_ENCRYPTION_KEY not set — encryption disabled.")
            return

        key_buf = bytearray(raw_key.encode())
        try:
            self._fernet  = Fernet(bytes(key_buf))
            self._enabled = True
            print("[crypto] Encryption enabled (Fernet / AES-128-CBC + HMAC-SHA256).")
        except Exception as exc:
            print(f"[crypto] Invalid key ({exc}) — encryption disabled.")
        finally:
            _secure_wipe_bytes(key_buf)  # zero key material from memory

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── Core primitives ───────────────────────────────────────────────────────

    def encrypt(self, data: bytes) -> bytes:
        if not self._enabled:
            return data
        return self._fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        if not self._enabled:
            return data
        try:
            return self._fernet.decrypt(data)
        except InvalidToken as exc:
            raise ValueError("Decryption failed — wrong key or corrupted data.") from exc

    def encrypt_str(self, text: str) -> str:
        return self.encrypt(text.encode()).decode()

    def decrypt_str(self, ciphertext: str) -> str:
        return self.decrypt(ciphertext.encode()).decode()

    # ── File helpers ──────────────────────────────────────────────────────────

    def encrypt_file(self, src: Path, dst: Path) -> None:
        dst.write_bytes(self.encrypt(src.read_bytes()))

    def decrypt_file(self, src: Path, dst: Path) -> None:
        dst.write_bytes(self.decrypt(src.read_bytes()))

    # ── Key management ────────────────────────────────────────────────────────

    @staticmethod
    def generate_key() -> str:
        if not _CRYPTO_OK:
            raise RuntimeError("'cryptography' package not installed.")
        return Fernet.generate_key().decode()
