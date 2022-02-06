from __future__ import annotations

from typing import TYPE_CHECKING, Union

from botbase import MyContext, MyInter
from nextcord import (
    SlashOption,
    StageChannel,
    VoiceChannel,
    slash_command,
    ChannelType,
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
        assert isinstance(channel, (VoiceChannel, StageChannel))
        # if channel is None:
        #     channel = ctx.author.voice.channel

        # await channel.connect(cls=Player)
        ...


def setup(bot: MyBot):
    bot.add_cog(Music(bot))
