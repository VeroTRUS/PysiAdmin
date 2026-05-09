"""
PysiAdmin — commands/exec.py
0.2.0: .exec-raw now requires .confirm <token> when confirm_exec_raw=true in config.
"""

from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from core.auth import Tier, require_tier

TIMEOUT_SECONDS = 30

BLOCKED_PATTERNS = [
    "/etc/shadow", "/etc/gshadow", "/etc/sudoers", "/etc/sudoers.d",
    "/root/", "/proc/kcore", "/proc/sysrq-trigger",
    "/dev/mem", "/dev/kmem", "/dev/sda", "/dev/nvme",
    "ssh_host_", ".ssh/id_", ".ssh/authorized_keys", ".gnupg/",
    "DISCORD_BOT_TOKEN", "BOT_TOKEN", ".env", "pysi-config",
    "/etc/passwd", "/etc/group", "/etc/crypttab",
    "/boot/", "/sys/firmware",
    # BSD-specific sensitive paths
    "/etc/master.passwd",   # OpenBSD / FreeBSD shadow equivalent
    "/etc/spwd.db",
    "/etc/pwd.db",
    "/etc/pf.conf",         # firewall rules
    "/boot/loader.conf",
    "/boot/kernel",
]

BLOCKED_COMMANDS = {
    "rm", "rmdir", "shred", "unlink",
    "dd", "mkfs", "fdisk", "parted", "gdisk", "wipefs",
    "chmod", "chown", "chgrp",
    "sudo", "su", "pkexec", "doas", "newgrp",
    "passwd", "useradd", "userdel", "usermod", "groupadd", "groupdel",
    "iptables", "ip6tables", "nftables", "firewall-cmd", "ufw",
    "pfctl",    # BSD firewall — read-only pfctl -s is in whitelist
    "wget", "curl",
    "nc", "ncat", "socat", "netcat",
    "python", "python3", "perl", "ruby", "lua", "php",
    "bash", "sh", "zsh", "fish", "dash", "ksh", "csh", "tcsh",
    "crontab", "at", "batch",
    "ssh", "scp", "sftp", "rsync",
    "sysctl",
    "modprobe", "rmmod", "insmod",
    "mount", "umount",
    "systemctl", "journalctl", "service", "rcctl",
    "strace", "ltrace", "gdb", "lldb", "truss", "kdump",  # truss/kdump = BSD strace
    "tcpdump", "wireshark", "tshark",
    "kill", "killall", "pkill",
    "reboot", "shutdown", "poweroff", "halt", "init",
    "format", "truncate",
    "visudo", "vipw",
    "chroot", "jail",       # jail = BSD chroot equivalent
    "unshare", "nsenter",
    "docker", "podman", "kubectl",
    "kldload", "kldunload",  # BSD kernel module load/unload
}


class ExecCommands(commands.Cog, name="Execution"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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
        base = command.strip().split()[0].split("/")[-1]
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

    @commands.command(name="exec")
    @require_tier(Tier.ADMIN)
    async def exec_cmd(self, ctx: commands.Context, *, command: str) -> None:
        mode = self.bot.settings.exec_mode

        hit, pat = self._contains_blocked_pattern(command)
        if hit:
            await ctx.send(embed=self._denied("⛔ Blocked Pattern", f"References: `{pat}`"))
            await self.bot.audit.log_command(str(ctx.author.id), f".exec {command}", "DENIED", f"blocked_pattern={pat!r}")
            return

        if mode == "whitelist":
            if not self._whitelisted(command):
                await ctx.send(embed=self._denied(
                    "⛔ Not Whitelisted",
                    f"`{command}` not in `exec_whitelist`.\nEdit `pysi-config.json` to add it.",
                ))
                await self.bot.audit.log_command(str(ctx.author.id), f".exec {command}", "DENIED", "not whitelisted")
                return
        elif mode == "denylist":
            hit_cmd, base = self._contains_blocked_command(command)
            if hit_cmd:
                await ctx.send(embed=self._denied("⛔ Blocked Command", f"`{base}` is permanently blocked."))
                await self.bot.audit.log_command(str(ctx.author.id), f".exec {command}", "DENIED", f"blocked_cmd={base!r}")
                return

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
        await self.bot.audit.log_command(str(ctx.author.id), f".exec {command}", "OK", f"rc={rc}")

    @commands.command(name="exec-raw")
    @require_tier(Tier.OWNER)
    async def exec_raw(self, ctx: commands.Context, *, command: str) -> None:
        """Run any command. If confirm_exec_raw=true, requires .confirm <token>."""
        hit, pat = self._contains_blocked_pattern(command)
        if hit:
            await ctx.send(embed=self._denied(
                "⛔ Blocked Pattern",
                f"References: `{pat}`\nEdit `commands/exec.py` on disk to override.",
            ))
            await self.bot.audit.log_command(str(ctx.author.id), f".exec-raw {command}", "DENIED", f"blocked_pattern={pat!r}")
            return

        if self.bot.settings.confirm_exec_raw:
            # Store pending confirmation and require .confirm <token>
            uid = str(ctx.author.id)

            async def _execute():
                await self.bot.audit.log_command(uid, f".exec-raw {command}", "EXECUTING")
                rc, out, err = await self._run(command)
                output = self._format_output(out, err)
                embed = discord.Embed(
                    title=f"👑 exec-raw  (rc={rc})",
                    color=discord.Color.green() if rc == 0 else discord.Color.orange(),
                )
                embed.add_field(name="Command", value=f"`{command}`",        inline=False)
                embed.add_field(name="Output",  value=f"```\n{output}\n```", inline=False)
                await ctx.send(embed=embed)
                await self.bot.audit.log_command(uid, f".exec-raw {command}", "OK", f"rc={rc}")

            token = self.bot.sessions.create(
                user_id    = uid,
                command    = command,
                callback   = _execute,
                channel_id = ctx.channel.id,
                ttl        = 30,
            )
            await ctx.send(embed=discord.Embed(
                title="⚠️ Confirmation Required",
                description=(
                    f"Command: `{command}`\n\n"
                    f"Type `.confirm {token}` within **30 seconds** to execute.\n"
                    "Type `.cancel` to abort."
                ),
                color=discord.Color.gold(),
            ))
            await self.bot.audit.log_command(uid, f".exec-raw {command}", "PENDING_CONFIRM", f"token={token}")
        else:
            # confirm_exec_raw disabled — execute immediately
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
            await self.bot.audit.log_command(str(ctx.author.id), f".exec-raw {command}", "OK", f"rc={rc}")

    @commands.command(name="confirm")
    @require_tier(Tier.OWNER)
    async def confirm(self, ctx: commands.Context, token: str) -> None:
        """Confirm a pending .exec-raw operation."""
        uid   = str(ctx.author.id)
        entry = self.bot.sessions.consume(token, uid)
        if entry is None:
            await ctx.send(embed=discord.Embed(
                title="❌ Invalid or Expired Token",
                description="Token not found, already used, or expired (30s TTL).",
                color=discord.Color.red(),
            ))
            return
        await self.bot.audit.log_command(uid, f".confirm {token}", "OK", f"cmd={entry.command!r}")
        await entry.callback()

    @commands.command(name="cancel")
    @require_tier(Tier.OWNER)
    async def cancel(self, ctx: commands.Context) -> None:
        """Cancel all your pending confirmations."""
        n = self.bot.sessions.cancel(str(ctx.author.id))
        await ctx.send(f"✅ Cancelled {n} pending confirmation(s).")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ExecCommands(bot))
