"""
PysiAdmin — commands/process.py
Process listing and safe termination.
"""

from __future__ import annotations

import os

import discord
import psutil
from discord.ext import commands

from core.auth import Tier, require_tier


class ProcessCommands(commands.Cog, name="Process"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="ps")
    @require_tier(Tier.OBSERVER)
    async def ps(self, ctx: commands.Context) -> None:
        """List top 20 processes sorted by CPU usage."""
        procs: list[dict] = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: x.get("cpu_percent") or 0.0, reverse=True)

        header = f"{'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  {'STATUS':>10}  NAME"
        sep    = "-" * 56
        rows   = [
            f"{p['pid']:>7}  {p.get('cpu_percent') or 0:>6.1f}  "
            f"{p.get('memory_percent') or 0:>6.1f}  "
            f"{p.get('status', '?'):>10}  {p['name']}"
            for p in procs[:20]
        ]
        table = "\n".join(["```", header, sep] + rows + ["```"])

        embed = discord.Embed(title="📊 Process List (top 20 by CPU)", color=discord.Color.blue())
        embed.description = table
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(str(ctx.author.id), ".ps", "OK")

    @commands.command(name="kill")
    @require_tier(Tier.OPERATOR)
    async def kill(self, ctx: commands.Context, pid: int) -> None:
        """Send SIGTERM to a process by PID."""
        # Hard guards
        if pid == 1:
            await ctx.send("⛔ Refusing to kill PID 1 (init).")
            await self.bot.audit.log_command(str(ctx.author.id), f".kill {pid}", "DENIED", "PID 1 protected")
            return
        if pid == os.getpid():
            await ctx.send("⛔ Refusing to kill the agent itself. Use `.agent restart`.")
            await self.bot.audit.log_command(str(ctx.author.id), f".kill {pid}", "DENIED", "self-kill prevented")
            return

        try:
            proc = psutil.Process(pid)
            name = proc.name()
            proc.terminate()
            embed = discord.Embed(
                title="✅ SIGTERM Sent",
                description=f"PID `{pid}` (`{name}`) terminated.",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
            await self.bot.audit.log_command(str(ctx.author.id), f".kill {pid}", "OK", f"name={name}")
        except psutil.NoSuchProcess:
            await ctx.send(f"❌ No process with PID `{pid}`.")
            await self.bot.audit.log_command(str(ctx.author.id), f".kill {pid}", "ERROR", "NoSuchProcess")
        except psutil.AccessDenied:
            await ctx.send(f"❌ Access denied for PID `{pid}`.")
            await self.bot.audit.log_command(str(ctx.author.id), f".kill {pid}", "ERROR", "AccessDenied")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProcessCommands(bot))
