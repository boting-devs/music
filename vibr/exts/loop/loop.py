from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player


class Looptrack(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def looptrack(self, inter: MyInter) -> None:
        """Loop the current track again, and again, and again."""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        if not player.loop_track:
            player.loop_track = player.current
            player.looped_user = inter.user.id
            embed = Embed(
                title="Loop Mode On",
                description=f"{inter.user.mention} turned on loop mode",
                timestamp=utcnow(),
            )
            await inter.send(embed=embed)

        else:
            player.loop_track = None
            embed = Embed(
                title="Loop Mode Off",
                description=f"{inter.user.mention} turned off loop mode",
                timestamp=utcnow(),
            )


def setup(bot: Vibr) -> None:
    bot.add_cog(Looptrack(bot))
