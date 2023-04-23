from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from mafic import Filter, Timescale
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player


class Nightcore(CogBase[Vibr]):
    @slash_command(name="nightcore", dm_permission=False)
    @is_connected_and_playing
    async def nightcore(self, inter: MyInter) -> None:
        """A funny filter. Just Try it out!"""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        if await player.has_filter("nightcore"):
            await player.remove_filter("nightcore", fast_apply=True)
            embed = Embed(title="Nightcore Filter Deactivated")

        else:
            night = Timescale(speed=1.25, pitch=1.3)
            nightcore_filter = Filter(timescale=night)
            await player.add_filter(
                nightcore_filter, label="nightcore", fast_apply=True
            )
            embed = Embed(title="Nightcore Filter activated")

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Nightcore(bot))
