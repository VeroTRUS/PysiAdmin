"""
PysiAdmin — commands/config_cmd.py
Read and write a safe subset of pysi-config.json via bot.
Sensitive keys (owner_ids, etc.) must be edited on disk directly.
"""

from __future__ import annotations

import json

import discord
from discord.ext import commands

from core.auth import Tier, require_tier

# Keys visible via .config get (Admin+)
READABLE = {"exec_whitelist", "file_transfer_max_bytes", "log_dir", "log_channel_id"}

# Keys writable via .config set (Admin+) — no identity/ACL keys
WRITABLE = {"exec_whitelist", "file_transfer_max_bytes", "log_channel_id"}


class ConfigCommands(commands.Cog, name="Config"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group(name="config", invoke_without_command=True)
    @require_tier(Tier.ADMIN)
    async def config_group(self, ctx: commands.Context) -> None:
        await ctx.send("Usage: `.config get <key>` | `.config set <key> <value>`")

    @config_group.command(name="get")
    @require_tier(Tier.ADMIN)
    async def config_get(self, ctx: commands.Context, key: str) -> None:
        if key not in READABLE:
            await ctx.send(
                f"❌ `{key}` is not remotely readable. "
                "Edit `pysi-config.json` on disk."
            )
            return
        value = getattr(self.bot.settings, key, None)
        embed = discord.Embed(title=f"⚙️ config: {key}", color=discord.Color.blue())
        embed.add_field(
            name="Value",
            value=f"```json\n{json.dumps(value, indent=2)}\n```",
            inline=False,
        )
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(str(ctx.author.id), f".config get {key}", "OK")

    @config_group.command(name="set")
    @require_tier(Tier.ADMIN)
    async def config_set(self, ctx: commands.Context, key: str, *, value: str) -> None:
        if key not in WRITABLE:
            await ctx.send(
                f"❌ `{key}` is not remotely writable. "
                "Edit `pysi-config.json` on disk."
            )
            return
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value  # plain string fallback

        setattr(self.bot.settings, key, parsed)
        self.bot.settings.save()

        await ctx.send(f"✅ `{key}` updated and saved.")
        await self.bot.audit.log_command(
            str(ctx.author.id), f".config set {key}", "OK", f"value={value!r}"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ConfigCommands(bot))
