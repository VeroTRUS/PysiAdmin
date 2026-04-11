"""
screen.py -- PysiAdmin

Handlers for screenshot and screen-capture commands.
Both are Owner-tier only and fully logged via the audit chain.

    screenshot  -- single on-demand capture sent as a Discord attachment
    capture     -- managed periodic capture session (start/stop/status)
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import discord

import monitoring


async def screenshot(args, message, config, user_id) -> str:
    """Capture a single screenshot and send it as an attachment."""
    await message.reply("Capturing...")
    img = await monitoring.take_single_screenshot()

    if not img:
        await message.reply("Screenshot failed. Ensure `mss` is installed: `pip install mss`")
        return "error: screenshot failed"

    filename = f"screenshot_{int(time.time())}.png"
    await message.reply(
        "Screenshot attached.",
        file=discord.File(io.BytesIO(img), filename=filename),
    )
    return "screenshot"


async def capture(args, message, config, user_id) -> str:
    """
    Manage a periodic screen-capture session.

    .capture start [interval_seconds] [save_dir]
    .capture stop
    .capture status
    """
    sub = args[0].lower() if args else "status"

    if sub == "start":
        if len(args) > 1:
            if not args[1].isdigit():
                await message.reply("Interval must be a positive integer (seconds).")
                return "error: bad interval"
            interval = int(args[1])
        else:
            interval = 30

        if len(args) > 2:
            save_dir = Path(args[2])
            if (
                config.allowed_upload_roots
                and not monitoring.path_allowed(save_dir, config.allowed_upload_roots)
            ):
                save_dir = Path.home() / "pysi-captures" / str(int(time.time()))
        else:
            save_dir = Path.home() / "pysi-captures" / str(int(time.time()))

        msg = await monitoring.start_capture(interval, save_dir, user_id)
        await message.reply(msg)
        return "capture start"

    if sub == "stop":
        msg, _ = await monitoring.stop_capture()
        await message.reply(msg)
        return "capture stop"

    if sub == "status":
        await message.reply(await monitoring.capture_status())
        return "capture status"

    await message.reply(
        "Usage: `.capture start [interval_s] [dir]` | `.capture stop` | `.capture status`"
    )
    return f"error: unknown subcommand {sub}"
