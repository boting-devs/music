from __future__ import annotations

from botbase import CogBase, MyInter
from mafic import Player
from nextcord import StageChannel, VoiceChannel, slash_command

from vibr.bot import Vibr
from vibr.embed import Embed

from ._checks import already_connected, can_connect
from ._errors import UserNotInVoice


class Join(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @already_connected
    async def join(
        self, inter: MyInter, channel: VoiceChannel | StageChannel | None = None
    ) -> None:
        """Connect to your voice channel.

        channel:
            The channel to connect to. Leave blank to connect to your current channel.
        """
        if channel is None:
            channel = inter.user.voice and inter.user.voice.channel

            if channel is None:
                raise UserNotInVoice

        if not await can_connect(channel, inter=inter):
            return

        await channel.connect(cls=Player)

        embed = Embed(
            title="Connected!", description=f"Connected to {channel.mention}."
        )
        await inter.response.send_message(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Join(bot))
