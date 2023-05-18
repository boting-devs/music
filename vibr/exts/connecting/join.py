from __future__ import annotations

from botbase import CogBase
from nextcord import StageChannel, VoiceChannel, slash_command

from vibr.bot import Vibr
from vibr.inter import Inter

from ._checks import already_connected


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
        # Defer in case we want to send an error message.
        # No need to clutter the channel with a public error message.
        await inter.response.defer(ephemeral=True)

        await self.bot.join(inter=inter, channel=channel)

        await inter.delete_original_message()


def setup(bot: Vibr) -> None:
    bot.add_cog(Join(bot))
