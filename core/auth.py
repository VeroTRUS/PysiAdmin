"""
PysiAdmin — core/auth.py
Permission tiers and the require_tier() check decorator.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Optional

import discord
from discord.ext import commands

from config.settings import Settings


class Tier(IntEnum):
    OBSERVER = 1
    OPERATOR = 2
    ADMIN    = 3
    OWNER    = 4


TIER_LABELS = {
    Tier.OBSERVER: "🔍 Observer",
    Tier.OPERATOR: "🔧 Operator",
    Tier.ADMIN:    "⚙️ Admin",
    Tier.OWNER:    "👑 Owner",
}


class AuthManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_tier(self, user_id: str) -> Optional[Tier]:
        if user_id in self.settings.owner_ids:
            return Tier.OWNER
        if user_id in self.settings.admin_ids:
            return Tier.ADMIN
        if user_id in self.settings.operator_ids:
            return Tier.OPERATOR
        if user_id in self.settings.observer_ids:
            return Tier.OBSERVER
        return None

    def require(self, user_id: str, min_tier: Tier) -> bool:
        tier = self.get_tier(user_id)
        return tier is not None and tier >= min_tier

    def label(self, user_id: str) -> str:
        tier = self.get_tier(user_id)
        if tier is None:
            return "⛔ Unauthorized"
        return TIER_LABELS[tier]


def require_tier(min_tier: Tier):
    """Reusable command check decorator for all cogs."""
    async def predicate(ctx: commands.Context) -> bool:
        auth: AuthManager = ctx.bot.auth
        if not auth.require(str(ctx.author.id), min_tier):
            embed = discord.Embed(
                title="⛔ Insufficient Permission",
                description=f"This command requires tier: **{min_tier.name}**",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return False
        return True
    return commands.check(predicate)
