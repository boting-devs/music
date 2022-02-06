from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import MyContext
from nextcord import (
    User,
    Member,
)
from nextcord.ext.commands import Cog, command
from pomice import Player

from nextcord import User, ClientUser
from nextcord.ext.commands import BotMissingPermissions, NoPrivateMessage

from .extras.errors import NotInVoice

if TYPE_CHECKING:
    from ..mmain import MyBot


class Music(Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    def cog_check(self, ctx: MyContext) -> bool:
        if (
            ctx.guild is None
            or isinstance(ctx.author, User)
            or isinstance(ctx.me, ClientUser)
        ):
            raise NoPrivateMessage()
        elif ctx.author.voice is None or ctx.author.voice.channel is None:
            raise NotInVoice()
        elif (
            not ctx.author.voice.channel.permissions_for(ctx.me).connect
            and not ctx.author.voice.channel.permissions_for(ctx.me).administrator
        ):
            raise BotMissingPermissions(["connect"])

        return True

    @command(
        name="join", help="Join your voice channel.", aliases=["connect", "c", "j"]
    )
    async def join_prefix(self, ctx: MyContext):
        assert isinstance(ctx.author, Member) and ctx.author.voice is not None and ctx.author.voice.channel is not None

        channel = ctx.author.voice.channel

        await channel.connect(cls=Player)  # type: ignore

        await ctx.send("Logic for connected.")


def setup(bot: MyBot):
    bot.add_cog(Music(bot))
