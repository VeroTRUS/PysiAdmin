"""
PysiAdmin — compat/platform.py
Runtime OS detection and platform-specific capability flags.
Used throughout the codebase to branch on Linux vs BSD.
"""

from __future__ import annotations

import platform
import shutil

_SYS = platform.system()

IS_LINUX   = _SYS == "Linux"
IS_FREEBSD = _SYS == "FreeBSD"
IS_OPENBSD = _SYS == "OpenBSD"
IS_NETBSD  = _SYS == "NetBSD"
IS_BSD     = IS_FREEBSD or IS_OPENBSD or IS_NETBSD

# eBPF is Linux-only; DTrace is available on all BSD systems
EBPF_AVAILABLE  = IS_LINUX
DTRACE_AVAILABLE = IS_BSD and shutil.which("dtrace") is not None

# Package manager per platform
if IS_LINUX:
    # Best-effort detection — callers should not rely on this for security
    import shlex, subprocess
    def _detect_pm() -> str:
        for pm in ("dnf", "apt", "pacman", "zypper", "emerge", "eopkg"):
            if shutil.which(pm):
                return pm
        return "unknown"
    PKG_MANAGER = _detect_pm()
elif IS_FREEBSD:
    PKG_MANAGER = "pkg"
elif IS_OPENBSD:
    PKG_MANAGER = "pkg_add"
elif IS_NETBSD:
    PKG_MANAGER = "pkgin"
else:
    PKG_MANAGER = "unknown"

# Human-readable OS label
OS_LABEL: str = {
    "Linux":   f"Linux ({platform.freedesktop_os_release().get('NAME', 'unknown')})"
               if IS_LINUX and hasattr(platform, 'freedesktop_os_release')
               else "Linux",
    "FreeBSD": f"FreeBSD {platform.release()}",
    "OpenBSD": f"OpenBSD {platform.release()}",
    "NetBSD":  f"NetBSD {platform.release()}",
}.get(_SYS, _SYS)


# ── BSD-specific default whitelist additions ──────────────────────────────────

BSD_EXEC_WHITELIST: list[str] = [
    # Network — BSD uses ifconfig, sockstat instead of ip/ss
    "ifconfig",
    "ifconfig -a",
    "netstat -an",
    "netstat -rn",
    "sockstat",
    "sockstat -l",

    # Process / system
    "fstat",
    "procstat",
    "sysctl",
    "sysctl -a",
    "vmstat",
    "systat",

    # Disk
    "gpart show",        # FreeBSD disk layout
    "disklabel",         # OpenBSD/NetBSD disk layout
    "mount",

    # Services
    "service -e",        # FreeBSD: list enabled services
    "service -l",        # FreeBSD: list all services
    "rcctl ls all",      # OpenBSD: list all services
    "rcctl ls started",  # OpenBSD: list running services

    # Packages
    "pkg info",          # FreeBSD
    "pkg_info",          # OpenBSD / NetBSD
    "pkgin list",        # NetBSD

    # Logs (syslog on BSD, not journalctl)
    "tail -n 50 /var/log/messages",
    "tail -n 50 /var/log/auth.log",
    "tail -n 50 /var/log/daemon",
    "dmesg",
]

FREEBSD_EXEC_WHITELIST: list[str] = BSD_EXEC_WHITELIST + [
    "pkg version",
    "pkg audit",
    "bsdstat",
    "top -SH",
    "gstat",
]

OPENBSD_EXEC_WHITELIST: list[str] = BSD_EXEC_WHITELIST + [
    "pfctl -s rules",
    "pfctl -s state",
    "pfctl -s info",
    "pkg_check",
    "syspatch -c",   # list pending patches
]

NETBSD_EXEC_WHITELIST: list[str] = BSD_EXEC_WHITELIST + [
    "pkgin update",
    "pkgin search",
]


def platform_exec_whitelist() -> list[str]:
    """Return platform-specific whitelist additions to merge into config."""
    if IS_FREEBSD:
        return FREEBSD_EXEC_WHITELIST
    if IS_OPENBSD:
        return OPENBSD_EXEC_WHITELIST
    if IS_NETBSD:
        return NETBSD_EXEC_WHITELIST
    return []
