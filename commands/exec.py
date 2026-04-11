"""
PysiAdmin — commands/exec.py
.exec      — Admin tier, whitelist-only + blocked-pattern guard
.exec-raw  — Owner tier, blocked-pattern guard only (no whitelist)
"""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from core.auth import Tier, require_tier

TIMEOUT_SECONDS = 30

# Paths and tokens that must never appear in any executed command,
# even for Owner tier via .exec-raw.
BLOCKED_PATTERNS = [
    "/etc/shadow",
    "/etc/gshadow",
    "/etc/sudoers",
    "/etc/sudoers.d",
    "/root/",
    "/proc/kcore",
    "/proc/sysrq-trigger",
    "/dev/mem",
    "/dev/kmem",
    "/dev/sda",
    "/dev/nvme",
    "ssh_host_",
    ".ssh/id_",
    ".ssh/authorized_keys",
    ".gnupg/",
    "DISCORD_BOT_TOKEN",
    "BOT_TOKEN",
    ".env",
    "pysi-config",
    "/etc/passwd",
    "/etc/group",
    "/etc/crypttab",
    "/boot/",
    "/sys/firmware",
]


class ExecCommands(commands.Cog, name="Execution"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── Internal helpers ──────────────────────────────────────────────────────

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

    def _whitelisted(self, command: str) -> bool:
        """
        Return True if `command` matches a whitelist entry exactly
        or starts with a whitelist entry followed by a space (i.e. has args).
        """
        cmd = command.strip()
        for entry in self.bot.settings.exec_whitelist:
            if cmd == entry or cmd.startswith(entry + " "):
                return True
        return False

    def _contains_blocked(self, command: str) -> tuple[bool, str]:
        """
        Return (True, matched_pattern) if command references a blocked path
        or token. Case-insensitive. Applied to BOTH .exec and .exec-raw.
        """
        cmd_lower = command.lower()
        for pat in BLOCKED_PATTERNS:
            if pat.lower() in cmd_lower:
                return True, pat
        return False, ""

    def _format_output(self, out: str, err: str, max_len: int = 1850) -> str:
        combined = out
        if err:
            combined += f"\n[stderr]\n{err}"
        combined = combined.strip() or "(no output)"
        if len(combined) > max_len:
            combined = combined[:max_len] + "\n… (truncated)"
        return combined

    def _denied_embed(self, title: str, description: str) -> discord.Embed:
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red(),
        )

    # ── Commands ──────────────────────────────────────────────────────────────

    @commands.command(name="exec")
    @require_tier(Tier.ADMIN)
    async def exec_cmd(self, ctx: commands.Context, *, command: str) -> None:
        """Execute a whitelisted shell command (Admin+)."""

        # 1. Blocked-pattern guard — checked before whitelist
        blocked, pattern = self._contains_blocked(command)
        if blocked:
            await ctx.send(embed=self._denied_embed(
                "⛔ Blocked Pattern",
                f"Command references a protected path or token: `{pattern}`",
            ))
            await self.bot.audit.log_command(
                str(ctx.author.id), f".exec {command}", "DENIED",
                f"blocked pattern={pattern!r}",
            )
            return

        # 2. Whitelist check
        if not self._whitelisted(command):
            await ctx.send(embed=self._denied_embed(
                "⛔ Not Whitelisted",
                f"`{command}` is not in `exec_whitelist`.\n"
                "Edit `pysi-config.json` on disk to add it.",
            ))
            await self.bot.audit.log_command(
                str(ctx.author.id), f".exec {command}", "DENIED", "not whitelisted",
            )
            return

        # 3. Execute
        await self.bot.audit.log_command(
            str(ctx.author.id), f".exec {command}", "EXECUTING"
        )
        rc, out, err = await self._run(command)
        output = self._format_output(out, err)

        embed = discord.Embed(
            title=f"⚙️ exec  (rc={rc})",
            color=discord.Color.green() if rc == 0 else discord.Color.orange(),
        )
        embed.add_field(name="Command", value=f"`{command}`",        inline=False)
        embed.add_field(name="Output",  value=f"```\n{output}\n```", inline=False)
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(
            str(ctx.author.id), f".exec {command}", "OK", f"rc={rc}"
        )

    @commands.command(name="exec-raw")
    @require_tier(Tier.OWNER)
    async def exec_raw(self, ctx: commands.Context, *, command: str) -> None:
        """Execute any shell command — blocked-pattern guard still applies (Owner only)."""

        # Blocked-pattern guard applies even to Owner tier
        blocked, pattern = self._contains_blocked(command)
        if blocked:
            await ctx.send(embed=self._denied_embed(
                "⛔ Blocked Pattern",
                f"Command references a protected path or token: `{pattern}`\n"
                "Remove the pattern from `BLOCKED_PATTERNS` in `exec.py` on disk if you truly need this.",
            ))
            await self.bot.audit.log_command(
                str(ctx.author.id), f".exec-raw {command}", "DENIED",
                f"blocked pattern={pattern!r}",
            )
            return

        await self.bot.audit.log_command(
            str(ctx.author.id), f".exec-raw {command}", "EXECUTING"
        )
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
