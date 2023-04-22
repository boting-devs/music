from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from mafic.filter import Filter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player


class BassBoost(Filter):
    def __init__(self) -> None:
        super().__init__(
            equalizer=[
                -0.075,
                0.175,
                0.175,
                0.15,
                0.05,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.15,
                0.175,
                0.05,
            ]
        )


class Bass(CogBase[Vibr]):
    @slash_command(name="bass-boost", dm_permission=False)
    @is_connected_and_playing
    async def bass(self, inter: MyInter) -> None:
        """Toggle the bass-boost filter."""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        if await player.has_filter("bassboost"):
            await player.remove_filter("bassboost", fast_apply=True)
            embed = Embed(title="Bass-Boost Filter Deactivated")
        else:
            await player.add_filter(BassBoost(), label="bassboost", fast_apply=True)
            embed = Embed(title="Bass-Boost Filter Activated")

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Bass(bot))
