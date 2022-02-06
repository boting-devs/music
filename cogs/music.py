from __future__ import annotations

from typing import TYPE_CHECKING, Union

from pomice import Player
from botbase import MyContext
from nextcord import VoiceChannel, StageChannel, slash_command, SlashOption, Interaction
from nextcord.ext.commands import Cog, command

if TYPE_CHECKING:
    from ..mmain import MyBot


class Music(Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @command(
        name="join", help="Join your voice channel.", aliases=["connect", "c", "j"]
    )
    async def join_prefix(
        self, ctx: MyContext, channel: Union[VoiceChannel, StageChannel] = None
    ):
        await self.join(ctx, channel)

    @slash_command(name="join", description="Join your voice channel.")
    async def join_slash(self, inter: Interaction, channel: VoiceChannel | StageChannel | None):
        await self.join(inter, channel)

    async def join(self, aaa: Interaction | MyContext, channel: VoiceChannel | StageChannel | None):
        # if channel is None:
        #     channel = ctx.author.voice.channel

        # await channel.connect(cls=Player)
        ...


def setup(bot: MyBot):
    bot.add_cog(Music(bot))
