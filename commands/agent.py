"""
PysiAdmin — commands/agent.py
Agent self-management: restart, log tailing, process stats.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import discord
import psutil
from discord.ext import commands

from core.auth import Tier, require_tier


class AgentCommands(commands.Cog, name="Agent"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group(name="agent", invoke_without_command=True)
    @require_tier(Tier.OWNER)
    async def agent_group(self, ctx: commands.Context) -> None:
        await ctx.send(
            "**Agent commands:**\n"
            "`.agent status` — memory / CPU / uptime of this process\n"
            "`.agent logs [n]` — tail last N lines of today's audit log\n"
            "`.agent restart` — graceful restart via os.execv"
        )

    @agent_group.command(name="status")
    @require_tier(Tier.OWNER)
    async def agent_status(self, ctx: commands.Context) -> None:
        proc      = psutil.Process(os.getpid())
        mem       = proc.memory_info()
        cpu       = proc.cpu_percent(interval=0.2)
        uptime_s  = int(time.time() - proc.create_time())
        h, rem    = divmod(uptime_s, 3600)
        m, s      = divmod(rem, 60)

        embed = discord.Embed(title="🤖 Agent Process", color=discord.Color.green())
        embed.add_field(name="PID",     value=str(os.getpid()),             inline=True)
        embed.add_field(name="CPU%",    value=f"{cpu}%",                    inline=True)
        embed.add_field(name="RSS",     value=f"{mem.rss // 1024**2} MB",   inline=True)
        embed.add_field(name="Uptime",  value=f"{h}h {m}m {s}s",           inline=True)
        embed.add_field(name="Python",  value=sys.version.split()[0],       inline=True)
        await ctx.send(embed=embed)

    @agent_group.command(name="logs")
    @require_tier(Tier.OWNER)
    async def agent_logs(self, ctx: commands.Context, n: int = 50) -> None:
        """Tail the last N lines of today's audit log (max 100)."""
        n = min(n, 100)
        today    = datetime.now(timezone.utc).strftime("%Y%m%d")
        log_file = Path(self.bot.settings.log_dir) / f"pysi_admin_{today}.log"

        if not log_file.exists():
            await ctx.send("❌ No audit log for today yet.")
            return

        lines = log_file.read_text(errors="replace").splitlines()
        tail  = "\n".join(lines[-n:]) or "(empty)"
        if len(tail) > 1900:
            tail = tail[-1900:]

        await ctx.send(f"```\n{tail}\n```")
        await self.bot.audit.log_command(str(ctx.author.id), f".agent logs {n}", "OK")

    @agent_group.command(name="restart")
    @require_tier(Tier.OWNER)
    async def agent_restart(self, ctx: commands.Context) -> None:
        """Restart the agent process via os.execv (no daemon required)."""
        await self.bot.audit.log_command(str(ctx.author.id), ".agent restart", "EXECUTING")
        await ctx.send("🔄 Restarting…")
        await self.bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AgentCommands(bot))
