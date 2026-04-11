"""
PysiAdmin — commands/system.py
Observer-tier read-only system commands.
"""

from __future__ import annotations

import platform
import socket
import time

import discord
import psutil
from discord.ext import commands

from core.auth import Tier, require_tier


class SystemCommands(commands.Cog, name="System"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="status")
    @require_tier(Tier.OBSERVER)
    async def status(self, ctx: commands.Context) -> None:
        """Quick health snapshot: CPU / RAM / Disk."""
        cpu  = psutil.cpu_percent(interval=0.5)
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        embed = discord.Embed(title="🖥️ System Status", color=discord.Color.green())
        embed.add_field(name="CPU",  value=f"{cpu}%", inline=True)
        embed.add_field(
            name="RAM",
            value=f"{mem.percent}%  ({mem.used // 1024**2} MB / {mem.total // 1024**2} MB)",
            inline=True,
        )
        embed.add_field(
            name="Disk /",
            value=f"{disk.percent}%  ({disk.used // 1024**3} GB / {disk.total // 1024**3} GB)",
            inline=True,
        )
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(str(ctx.author.id), ".status", "OK")

    @commands.command(name="sysinfo")
    @require_tier(Tier.OBSERVER)
    async def sysinfo(self, ctx: commands.Context) -> None:
        """Detailed host information."""
        uname    = platform.uname()
        uptime_s = int(time.time() - psutil.boot_time())
        h, rem   = divmod(uptime_s, 3600)
        m, s     = divmod(rem, 60)

        embed = discord.Embed(title="📋 System Info", color=discord.Color.blue())
        embed.add_field(name="Hostname",  value=socket.gethostname(), inline=True)
        embed.add_field(name="OS",        value=f"{uname.system} {uname.release}", inline=True)
        embed.add_field(name="Arch",      value=uname.machine, inline=True)
        embed.add_field(name="Processor", value=uname.processor or "N/A", inline=False)
        embed.add_field(name="Uptime",    value=f"{h}h {m}m {s}s", inline=True)
        embed.add_field(name="CPUs",      value=str(psutil.cpu_count(logical=True)), inline=True)
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(str(ctx.author.id), ".sysinfo", "OK")

    @commands.command(name="uptime")
    @require_tier(Tier.OBSERVER)
    async def uptime(self, ctx: commands.Context) -> None:
        uptime_s = int(time.time() - psutil.boot_time())
        h, rem   = divmod(uptime_s, 3600)
        m, s     = divmod(rem, 60)
        await ctx.send(f"⏱️ Uptime: **{h}h {m}m {s}s**")
        await self.bot.audit.log_command(str(ctx.author.id), ".uptime", "OK")

    @commands.command(name="whoami")
    @require_tier(Tier.OBSERVER)
    async def whoami(self, ctx: commands.Context) -> None:
        embed = discord.Embed(title="🪪 Identity", color=discord.Color.purple())
        embed.add_field(name="Discord User", value=str(ctx.author),        inline=True)
        embed.add_field(name="Discord ID",   value=str(ctx.author.id),     inline=True)
        embed.add_field(name="Tier",         value=self.bot.auth.label(str(ctx.author.id)), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="help")
    @require_tier(Tier.OBSERVER)
    async def help_cmd(self, ctx: commands.Context) -> None:
        tier = self.bot.auth.get_tier(str(ctx.author.id))
        embed = discord.Embed(title="📖 PysiAdmin Help", color=discord.Color.blurple())

        embed.add_field(
            name="🔍 Observer",
            value="```\n.status  .sysinfo  .uptime  .whoami  .ps\n```",
            inline=False,
        )
        if tier >= Tier.OPERATOR:
            embed.add_field(
                name="🔧 Operator",
                value="```\n.kill <pid>  .file ls <path>  .file download <path>\n```",
                inline=False,
            )
        if tier >= Tier.ADMIN:
            embed.add_field(
                name="⚙️ Admin",
                value="```\n.exec <cmd>  .file upload <dest>  .config get/set <key>\n```",
                inline=False,
            )
        if tier >= Tier.OWNER:
            embed.add_field(
                name="👑 Owner",
                value="```\n.exec-raw <cmd>  .agent restart/logs/status  .shutdown\n```",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="shutdown")
    @require_tier(Tier.OWNER)
    async def shutdown(self, ctx: commands.Context) -> None:
        """Disconnect and stop the agent."""
        await self.bot.audit.log_command(str(ctx.author.id), ".shutdown", "EXECUTING")
        await ctx.send("🔌 Shutting down PysiAdmin agent.")
        await self.bot.close()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SystemCommands(bot))
