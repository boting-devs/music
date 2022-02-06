from __future__ import annotations

from typing import TYPE_CHECKING, Union

from botbase import MyContext, MyInter, WrappedUser
from nextcord import (
    ChannelType,
    SlashOption,
    StageChannel,
    User,
    VoiceChannel,
    slash_command,
)
from nextcord.abc import GuildChannel
from nextcord.ext.commands import Cog, command
from pomice import Player

if TYPE_CHECKING:
    from ..mmain import MyBot


class Music(Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @command(
        name="join", help="Join your voice channel.", aliases=["connect", "c", "j"]
    )
    async def join_prefix(
        self, ctx: MyContext, channel: Union[VoiceChannel, StageChannel] = None):
            channel = ctx.author.voice.channel
            await channel.connect(cls=pomice.Player)

    @slash_command(
        name="join",
        description="Join your voice channel.",
        guild_ids=[939509053623795732],
    )
    async def join_slash(
        self,
        inter: MyInter,
        channel: GuildChannel = SlashOption(  # type: ignore
            description="Optional channel to connect",
            channel_types=[ChannelType.voice, ChannelType.stage_voice],
            required=False,
        ),
    ):
        await self.join(inter, channel)

    async def join(self, aaa: MyInter | MyContext, channel: GuildChannel | None):
        assert isinstance(channel, (VoiceChannel, StageChannel, type(None)))

        if isinstance(aaa.author, (WrappedUser, User)) or not aaa.guild:
            return await aaa.send("Logic for guild only.")

        if not aaa.author.voice or not aaa.author.voice.channel:
            return await aaa.send("Logic for not connected.")

        if not channel:
            channel = aaa.author.voice.channel

        if not channel.permissions_for(aaa.guild.me).connect:
            return await aaa.send("Logic for no permissions.")

        await channel.connect()

        await aaa.send("Logic for connected.")


def setup(bot: MyBot):
    bot.add_cog(Music(bot))
