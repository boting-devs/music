from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from mafic.filter import Equalizer
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player


class Bass(CogBase[Vibr]):
    @slash_command(name="bass-boost", dm_permission=False)
    @is_connected_and_playing
    async def bass(self, inter: MyInter) -> None:
        """Increase bass of song."""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        await player.add_filter(Equalizer, label="bassboost", fast_apply=True)
        embed = Embed(title="Bass-Boost Filter activated")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Bass(bot))
