#!/usr/bin/env python3
"""
PysiAdmin — Personal System Administration Agent
Copyright (C) 2026  opfts
Licensed under the GNU General Public License v3.0 or later.

Entry point. Run: python3 pysi_admin.py
"""

from __future__ import annotations

import asyncio
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config.settings import Settings
from core.auth import AuthManager
from core.logger import AuditLogger
from core.parser import CommandParser

load_dotenv()

EXTENSIONS = [
    "commands.system",
    "commands.process",
    "commands.files",
    "commands.exec",
    "commands.config_cmd",
    "commands.agent",
]


def build_bot(settings: Settings) -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True  # required in Discord Developer Portal

    bot = commands.Bot(
        command_prefix=".",
        intents=intents,
        help_command=None,  # we implement our own .help
    )

    # Attach shared services
    bot.settings    = settings
    bot.audit       = AuditLogger(settings)
    bot.auth        = AuthManager(settings)
    bot.cmd_parser  = CommandParser(settings)

    return bot


async def main() -> None:
    settings = Settings.load()

    if not settings.owner_ids:
        print("[PysiAdmin] WARNING: owner_ids is empty in pysi-config.json.")
        print("[PysiAdmin] No one can issue Owner-tier commands until you add your Discord user ID.")

    bot = build_bot(settings)

    for ext in EXTENSIONS:
        await bot.load_extension(ext)

    @bot.event
    async def on_ready() -> None:
        print(f"[PysiAdmin] Online as {bot.user} (ID: {bot.user.id})")
        print(f"[PysiAdmin] Owner IDs: {settings.owner_ids}")
        await bot.audit.log_system("agent_start", f"bot={bot.user}")

    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot:
            return
        if not message.content.startswith("."):
            return

        uid = str(message.author.id)
        tier = bot.auth.get_tier(uid)

        if tier is None:
            embed = discord.Embed(
                title="⛔ Unauthorized",
                description="You are not in the PysiAdmin user list.",
                color=discord.Color.red(),
            )
            await message.channel.send(embed=embed)
            await bot.audit.log_command(uid, message.content, "DENIED", "not in whitelist")
            return

        await bot.audit.log_command(uid, message.content, "RECEIVED", f"tier={tier.name}")
        await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=discord.Embed(
                title="❓ Unknown Command",
                description="Use `.help` to see available commands.",
                color=discord.Color.orange(),
            ))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(
                title="⚠️ Missing Argument",
                description=str(error),
                color=discord.Color.orange(),
            ))
        elif isinstance(error, commands.CheckFailure):
            pass  # already handled in require_tier
        else:
            await bot.audit.log_error("on_command_error", str(error))
            raise error

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token or token == "YOUR_TOKEN_HERE":
        sys.exit("[PysiAdmin] ERROR: Set DISCORD_BOT_TOKEN in .env")

    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
