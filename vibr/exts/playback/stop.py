from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter


class Stop(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def stop(self, inter: Inter) -> None:
        """Stop the player."""

        player = inter.guild.voice_client

        player.queue.clear()
        await player.stop()

        embed = Embed(
            title="Stopped",
        )
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Stop(bot))
