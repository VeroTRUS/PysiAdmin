"""
PysiAdmin — commands/files.py
File listing, download (host→Discord), and upload (Discord→host).
"""

from __future__ import annotations

from pathlib import Path

import aiofiles
import discord
from discord.ext import commands

from core.auth import Tier, require_tier


class FileCommands(commands.Cog, name="Files"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group(name="file", invoke_without_command=True)
    @require_tier(Tier.OBSERVER)
    async def file_group(self, ctx: commands.Context) -> None:
        await ctx.send(
            "**File commands:**\n"
            "`.file ls <path>` — list directory\n"
            "`.file download <path>` — send file to Discord\n"
            "`.file upload <dest_path>` — save attached file to host"
        )

    @file_group.command(name="ls")
    @require_tier(Tier.OPERATOR)
    async def file_ls(
        self,
        ctx: commands.Context,
        path: str = None,   # ← FIX: was "." which exposed agent CWD
    ) -> None:
        # Default to the home directory of the user running the agent,
        # never to the agent's working directory.
        if path is None:
            path = str(Path.home())

        if not self.bot.cmd_parser.validate_path(path):
            await ctx.send("❌ Invalid path.")
            return

        p = Path(path).expanduser().resolve()
        if not p.exists():
            await ctx.send(f"❌ `{p}` does not exist.")
            return

        if p.is_file():
            stat = p.stat()
            await ctx.send(f"📄 `{p}` — {stat.st_size:,} bytes")
            return

        try:
            entries = sorted(p.iterdir())
        except PermissionError:
            await ctx.send("❌ Permission denied.")
            return

        lines = [
            f"{'📁' if e.is_dir() else '📄'} {e.name}"
            for e in entries[:50]
        ] or ["(empty)"]

        embed = discord.Embed(title=f"📂 {p}", color=discord.Color.blue())
        embed.description = "\n".join(lines)
        if len(entries) > 50:
            embed.set_footer(text=f"Showing 50 of {len(entries)} entries.")
        await ctx.send(embed=embed)
        await self.bot.audit.log_command(str(ctx.author.id), f".file ls {path}", "OK")

    @file_group.command(name="download")
    @require_tier(Tier.OPERATOR)
    async def file_download(self, ctx: commands.Context, path: str) -> None:
        if not self.bot.cmd_parser.validate_path(path):
            await ctx.send("❌ Invalid path.")
            return

        p    = Path(path).expanduser().resolve()
        if not p.is_file():
            await ctx.send(f"❌ File `{p}` not found.")
            return

        size     = p.stat().st_size
        max_size = self.bot.settings.file_transfer_max_bytes

        if size > max_size:
            await ctx.send(
                f"❌ File too large ({size:,} bytes). Limit: {max_size:,} bytes."
            )
            await self.bot.audit.log_command(
                str(ctx.author.id), f".file download {path}", "DENIED", f"size={size}"
            )
            return

        await ctx.send(f"📤 Uploading `{p.name}` ({size:,} bytes)…")
        try:
            await ctx.send(file=discord.File(str(p)))
            await self.bot.audit.log_command(
                str(ctx.author.id), f".file download {path}", "OK", f"size={size}"
            )
        except Exception as exc:
            await ctx.send(f"❌ Upload failed: {exc}")
            await self.bot.audit.log_command(
                str(ctx.author.id), f".file download {path}", "ERROR", str(exc)
            )

    @file_group.command(name="upload")
    @require_tier(Tier.ADMIN)
    async def file_upload(self, ctx: commands.Context, dest_path: str) -> None:
        if not ctx.message.attachments:
            await ctx.send("❌ Attach a file to your message.")
            return
        if not self.bot.cmd_parser.validate_path(dest_path):
            await ctx.send("❌ Invalid destination path.")
            return

        attachment = ctx.message.attachments[0]
        dest = Path(dest_path).expanduser().resolve()

        if dest.exists():
            # TODO: confirmation flow
            await ctx.send(
                f"⚠️ `{dest}` already exists. Delete it on the host first."
            )
            await self.bot.audit.log_command(
                str(ctx.author.id), f".file upload {dest_path}", "DENIED", "would overwrite"
            )
            return

        try:
            data = await attachment.read()
            async with aiofiles.open(dest, "wb") as fh:
                await fh.write(data)
            await ctx.send(
                f"✅ Saved `{attachment.filename}` → `{dest}` ({len(data):,} bytes)."
            )
            await self.bot.audit.log_command(
                str(ctx.author.id), f".file upload {dest_path}", "OK", f"bytes={len(data)}"
            )
        except Exception as exc:
            await ctx.send(f"❌ Write failed: {exc}")
            await self.bot.audit.log_command(
                str(ctx.author.id), f".file upload {dest_path}", "ERROR", str(exc)
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FileCommands(bot))
