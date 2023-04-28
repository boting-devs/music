from __future__ import annotations

from botbase import CogBase
from mafic.filter import Filter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter


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
    async def bass(self, inter: Inter) -> None:
        """Toggle the bass-boost filter."""

        player = inter.guild.voice_client

        if await player.has_filter("bassboost"):
            await player.remove_filter("bassboost", fast_apply=True)
            embed = Embed(title="Bass-Boost Filter Deactivated")
        else:
            await player.add_filter(BassBoost(), label="bassboost", fast_apply=True)
            embed = Embed(title="Bass-Boost Filter Activated")

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Bass(bot))
