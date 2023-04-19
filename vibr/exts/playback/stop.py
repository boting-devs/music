from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player


class Stop(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def stop(self, inter: MyInter) -> None:
        """Stop the player"""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        player.queue = []
        await player.stop()

        embed = Embed(
            title="Stopped", description=f"{inter.user.mention} stopped the player"
        )
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Stop(bot))
