from nextcord.ext.commands import (
    BotMissingPermissions,
    Context,
    GuildChannelConverter,
    MissingPermissions,
    NoPrivateMessage,
    bot_has_guild_permissions,
    bot_has_permissions,
    check,
    has_guild_permissions,
    has_permissions,
)
from nextcord import ClientUser, User

__all__ = (
    "admin_owner_perms",
    "bot_admin_perms",
    "admin_owner_guild_perms",
    "bot_admin_guild_perms",
    "admin_owner_or_channel_perms",
    "bot_admin_or_channel_perms",
    "admin_owner_or_arg_perms",
    "bot_admin_or_arg_perms",
)


def admin_owner_perms(**perms: bool):
    """user has admin or is me or permissions"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None or isinstance(ctx.author, User):
            raise NoPrivateMessage()

        original = has_permissions(**perms).predicate
        if (
            ctx.author.guild_permissions.administrator
            or await ctx.bot.is_owner(ctx.author)
            or await original(ctx)
        ):
            return True
        else:
            raise MissingPermissions(list(perms.keys()))

    return check(extended_check)


def bot_admin_perms(**perms: bool):
    """bot is admin or has perms (channel based)"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None or isinstance(ctx.me, ClientUser):
            raise NoPrivateMessage()

        original = bot_has_permissions(**perms).predicate

        if ctx.me.guild_permissions.administrator or await original(ctx):
            return True
        else:
            raise BotMissingPermissions(list(perms.keys()))

    return check(extended_check)


def admin_owner_guild_perms(**perms: bool):
    """user is admin or me or permissions (guild based)"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None or isinstance(ctx.author, User):
            raise NoPrivateMessage()

        original = has_guild_permissions(**perms).predicate

        if (
            await ctx.bot.is_owner(ctx.author)
            or ctx.author.guild_permissions.administrator
            or await original(ctx)
        ):
            return True
        else:
            raise MissingPermissions(list(perms.keys()))

    return check(extended_check)


def bot_admin_guild_perms(**perms: bool):
    """bot is admin or perms (guild based)"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None or isinstance(ctx.author, User):
            raise NoPrivateMessage()

        original = bot_has_guild_permissions(**perms).predicate

        if (
            await ctx.bot.is_owner(ctx.author)
            or ctx.author.guild_permissions.administrator
            or await original(ctx)
        ):
            return True
        else:
            raise MissingPermissions(list(perms.keys()))

    return check(extended_check)


def admin_owner_or_channel_perms(channel: str, **perms: bool):
    """user is admin or me or has perms on channel"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None or isinstance(ctx.author, User):
            raise NoPrivateMessage()

        ch = await GuildChannelConverter().convert(ctx, channel)
        permissions = ch.permissions_for(ctx.author)

        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if (
            await ctx.bot.is_owner(ctx.author)
            or permissions.administrator
            or not missing
        ):
            return True
        else:
            raise MissingPermissions(missing)

    return check(extended_check)


def bot_admin_or_channel_perms(channel: str, **perms):
    """bot is admin or has perms on channel"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None or isinstance(ctx.me, ClientUser):
            raise NoPrivateMessage()

        ch = await GuildChannelConverter().convert(ctx, channel)
        permissions = ch.permissions_for(ctx.me)

        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if permissions.administrator or not missing:
            return True
        else:
            raise BotMissingPermissions(missing)

    return check(extended_check)


def admin_owner_or_arg_perms(arg: int, **perms: bool):
    """user is admin or me or has perms on channel"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None:
            raise NoPrivateMessage()

        ch = ctx.args[arg]
        permissions = ch.permissions_for(ctx.author)

        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if await ctx.bot.is_owner(ctx.author) or permissions.administrator or not missing:
            return True
        else:
            raise MissingPermissions(missing)

    return check(extended_check)


def bot_admin_or_arg_perms(arg: int, **perms):
    """bot is admin or has perms on channel"""

    async def extended_check(ctx: Context) -> bool:
        if ctx.guild is None or isinstance(ctx.me, ClientUser):
            raise NoPrivateMessage()

        ch = ctx.args[arg]
        permissions = ch.permissions_for(ctx.me)

        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if permissions.administrator or not missing:
            return True
        else:
            raise BotMissingPermissions(missing)

    return check(extended_check)
