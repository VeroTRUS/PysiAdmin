"""
PysiAdmin — commands/exec.py

Two execution modes (set exec_mode in pysi-config.json):

  "whitelist"  (default, safest)
      .exec only runs commands listed in exec_whitelist.

  "denylist"   (more freedom)
      .exec runs any command not matching BLOCKED_PATTERNS or
      BLOCKED_COMMANDS. exec_whitelist is ignored in this mode.

.exec-raw — Owner only. Bypasses whitelist/denylist entirely.
            BLOCKED_PATTERNS still apply even here.
"""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from core.auth import Tier, require_tier

TIMEOUT_SECONDS = 30

# ── Hardcoded blocked path/token patterns (apply to ALL tiers, ALL modes) ────
BLOCKED_PATTERNS = [
    "/etc/shadow", "/etc/gshadow", "/etc/sudoers", "/etc/sudoers.d",
    "/root/", "/proc/kcore", "/proc/sysrq-trigger",
    "/dev/mem", "/dev/kmem", "/dev/sda", "/dev/nvme",
    "ssh_host_", ".ssh/id_", ".ssh/authorized_keys", ".gnupg/",
    "DISCORD_BOT_TOKEN", "BOT_TOKEN", ".env", "pysi-config",
    "/etc/passwd", "/etc/group", "/etc/crypttab",
    "/boot/", "/sys/firmware",
]

# ── Blocked command prefixes in denylist mode ─────────────────────────────────
# These base commands are always refused regardless of arguments.
BLOCKED_COMMANDS = {
    "rm", "rmdir", "shred", "unlink",
    "dd", "mkfs", "fdisk", "parted", "gdisk", "wipefs",
    "chmod", "chown", "chgrp",
    "sudo", "su", "pkexec", "doas", "newgrp",
    "passwd", "useradd", "userdel", "usermod", "groupadd", "groupdel",
    "iptables", "ip6tables", "nftables", "firewall-cmd", "ufw",
    "wget", "curl",        # allow curl -I only via whitelist mode
    "nc", "ncat", "socat", "netcat",
    "python", "python3", "perl", "ruby", "lua", "php",
    "bash", "sh", "zsh", "fish", "dash", "ksh",
    "crontab", "at", "batch",
    "ssh", "scp", "sftp", "rsync",
    "sysctl",
    "modprobe", "rmmod", "insmod", "lsmod",
    "mount", "umount",     # read-only mount is in whitelist; denylist blocks write
    "systemctl",           # use .exec in whitelist mode for specific systemctl queries
    "journalctl",          # same
    "strace", "ltrace", "gdb", "lldb",
    "tcpdump", "wireshark", "tshark",
    "kill", "killall", "pkill",   # use .kill command instead
    "reboot", "shutdown", "poweroff", "halt", "init",
    "format", "truncate",
    "visudo", "vipw",
    "chroot", "unshare", "nsenter",
    "docker", "podman", "kubectl",
}


class ExecCommands(commands.Cog, name="Execution"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _run(self, command: str) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            proc.kill()
            return -1, "", f"Timed out after {TIMEOUT_SECONDS}s"
        return (
            proc.returncode or 0,
            stdout.decode(errors="replace"),
            stderr.decode(errors="replace"),
        )

    def _contains_blocked_pattern(self, command: str) -> tuple[bool, str]:
        cmd_lower = command.lower()
        for pat in BLOCKED_PATTERNS:
            if pat.lower() in cmd_lower:
                return True, pat
        return False, ""

    def _contains_blocked_command(self, command: str) -> tuple[bool, str]:
        """Check if the base command (first token) is in BLOCKED_COMMANDS."""
        base = command.strip().split()[0].split("/")[-1]  # strip path prefix too
        if base in BLOCKED_COMMANDS:
            return True, base
        return False, ""

    def _whitelisted(self, command: str) -> bool:
        cmd = command.strip()
        for entry in self.bot.settings.exec_whitelist:
            if cmd == entry or cmd.startswith(entry + " "):
                return True
        return False

    def _format_output(self, out: str, err: str, max_len: int = 1850) -> str:
        combined = out
        if err:
            combined += f"\n[stderr]\n{err}"
        combined = combined.strip() or "(no output)"
        if len(combined) > max_len:
            combined = combined[:max_len] + "\n… (truncated)"
        return combined

    def _denied(self, title: str, desc: str) -> discord.Embed:
        return discord.Embed(title=title, description=desc, color=discord.Color.red())

    # ── .exec ─────────────────────────────────────────────────────────────────

    @commands.command(name="exec")
    @require_tier(Tier.ADMIN)
    async def exec_cmd(self, ctx: commands.Context, *, command: str) -> None:
        """
        Run a shell command.
        Behaviour depends on exec_mode in pysi-config.json:
          whitelist — command must be in exec_whitelist
          denylist  — command must not match BLOCKED_PATTERNS or BLOCKED_COMMANDS
        """
        mode = self.bot.settings.exec_mode

        # 1. Blocked-pattern check — always first, regardless of mode
        hit, pat = self._contains_blocked_pattern(command)
        if hit:
            await ctx.send(embed=self._denied(
                "⛔ Blocked Pattern",
                f"References protected path/token: `{pat}`",
            ))
            await self.bot.audit.log_command(
                str(ctx.author.id), f".exec {command}", "DENIED", f"blocked_pattern={pat!r}"
            )
            return

        if mode == "whitelist":
            if not self._whitelisted(command):
                await ctx.send(embed=self._denied(
                    "⛔ Not Whitelisted",
                    f"`{command}` is not in `exec_whitelist`.\n"
                    "Edit `pysi-config.json` on disk to add it, or switch to denylist mode.",
                ))
                await self.bot.audit.log_command(
                    str(ctx.author.id), f".exec {command}", "DENIED", "not whitelisted"
                )
                return

        elif mode == "denylist":
            hit_cmd, base = self._contains_blocked_command(command)
            if hit_cmd:
                await ctx.send(embed=self._denied(
                    "⛔ Blocked Command",
                    f"`{base}` is in the permanent block list.\n"
                    "Use `.exec-raw` (Owner only) if you genuinely need this.",
                ))
                await self.bot.audit.log_command(
                    str(ctx.author.id), f".exec {command}", "DENIED", f"blocked_cmd={base!r}"
                )
                return

        else:
            await ctx.send(f"⚠️ Unknown exec_mode `{mode}` — check pysi-config.json.")
            return

        # 2. Execute
        await self.bot.audit.log_command(str(ctx.author.id), f".exec {command}", "EXECUTING")
        rc, out, err = await self._run(command)
        output = self._format_output(out, err)

        embed = discord.Embed(
            title=f"⚙️ exec [{mode}]  (rc={rc})",
            color=discord.Color.green() if rc == 0 else discord.Color.orange(),
        )
        embed.add_field(name="Command", value=f"`{command}`",        inline=False)
        embed.add_field(name="Output",  value=f"```\n{output}\n```", inline=False)
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(
            str(ctx.author.id), f".exec {command}", "OK", f"rc={rc}"
        )

    # ── .exec-raw ─────────────────────────────────────────────────────────────

    @commands.command(name="exec-raw")
    @require_tier(Tier.OWNER)
    async def exec_raw(self, ctx: commands.Context, *, command: str) -> None:
        """Run any command — BLOCKED_PATTERNS still apply. Owner only."""
        hit, pat = self._contains_blocked_pattern(command)
        if hit:
            await ctx.send(embed=self._denied(
                "⛔ Blocked Pattern",
                f"References protected path/token: `{pat}`\n"
                "Edit `BLOCKED_PATTERNS` in `commands/exec.py` on disk to override.",
            ))
            await self.bot.audit.log_command(
                str(ctx.author.id), f".exec-raw {command}", "DENIED", f"blocked_pattern={pat!r}"
            )
            return

        await self.bot.audit.log_command(str(ctx.author.id), f".exec-raw {command}", "EXECUTING")
        rc, out, err = await self._run(command)
        output = self._format_output(out, err)

        embed = discord.Embed(
            title=f"👑 exec-raw  (rc={rc})",
            color=discord.Color.green() if rc == 0 else discord.Color.orange(),
        )
        embed.add_field(name="Command", value=f"`{command}`",        inline=False)
        embed.add_field(name="Output",  value=f"```\n{output}\n```", inline=False)
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(
            str(ctx.author.id), f".exec-raw {command}", "OK", f"rc={rc}"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ExecCommands(bot))
