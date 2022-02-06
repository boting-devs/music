from nextcord import Member, User, ClientUser
from nextcord.ext.commands import (
    BotMissingPermissions,
    Context,
    MissingPermissions,
    NoPrivateMessage,
    bot_has_guild_permissions,
    bot_has_permissions,
    check,
    has_guild_permissions,
    has_permissions,
)

from .errors import NotInVoice

__all__ = (
    "admin_owner_perms",
    "bot_admin_perms",
    "admin_owner_guild_perms",
    "bot_admin_guild_perms",
)


def admin_owner_perms(**perms: bool):
    """user has admin or is me or permissions"""

    async def extended_check(ctx: Context):
        if ctx.guild is None:
            raise NoPrivateMessage()
        original = has_permissions(**perms).predicate
        return (
            ctx.author.guild_permissions.administrator  # type: ignore
            or ctx.bot.is_owner(ctx.author)
            or await original(ctx)
        )

    return check(extended_check)


def bot_admin_perms(**perms: bool):
    """bot is admin or has perms (channel based)"""

    async def extended_check(ctx: Context):
        if ctx.guild is None:
            raise NoPrivateMessage()
        original = bot_has_permissions(**perms).predicate
        return ctx.me.guild_permissions.administrator or await original(  # type: ignore
            ctx
        )

    return check(extended_check)


def admin_owner_guild_perms(**perms: bool):
    """user is admin or me or permissions (guild based)"""

    async def extended_check(ctx: Context):
        if ctx.guild is None:
            raise NoPrivateMessage()
        original = has_guild_permissions(**perms).predicate
        return (
            ctx.author.guild_permissions.administrator  # type: ignore
            or ctx.bot.is_owner(ctx.author)
            or await original(ctx)
        )

    return check(extended_check)


def bot_admin_guild_perms(**perms: bool):
    """bot is admin or perms (guild based)"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None:
            raise NoPrivateMessage()
        original = bot_has_guild_permissions(**perms).predicate
        return ctx.me.guild_permissions.administrator or await original(  # type: ignore
            ctx
        )

    return check(extended_check)
