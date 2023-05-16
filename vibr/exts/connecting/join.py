from __future__ import annotations

from botbase import CogBase
from nextcord import StageChannel, VoiceChannel, slash_command

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter
from vibr.player import Player

from ._checks import already_connected, can_connect
from ._errors import UserNotInVoice


class Join(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @already_connected
    async def join(
        self, inter: Inter, channel: VoiceChannel | StageChannel | None = None
    ) -> None:
        """Connect to your voice channel.

        channel:
            The channel to connect to. Leave blank to connect to your current channel.
        """
        if not inter.response.is_done():
            # Defer in case we want to send an error message.
            # No need to clutter the channel with a public error message.
            await inter.response.defer(ephemeral=True)

        if channel is None:
            channel = inter.user.voice and inter.user.voice.channel

            if channel is None:
                raise UserNotInVoice

        if not await can_connect(channel, inter=inter):
            return

        player = await channel.connect(cls=Player, timeout=5)

        await self.bot.set_player_settings(player, channel.id)

        embed = Embed(
            title="Connected!", description=f"Connected to {channel.mention}."
        )

        await inter.channel.send(embed=embed)  # pyright: ignore
        await inter.delete_original_message()


def setup(bot: Vibr) -> None:
    bot.add_cog(Join(bot))
