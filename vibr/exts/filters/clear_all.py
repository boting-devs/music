from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

from ._error import NoFilterActive

if TYPE_CHECKING:
    from vibr.player import Player


class ClearAll(CogBase[Vibr]):
    @slash_command(name="clear-filters", dm_permission=False)
    @is_connected_and_playing
    async def clear_filters(self, inter: MyInter) -> None:
        """Clear all filters."""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        filters = ["nightcore", "rotate", "bassboost"]
        for i in filters:
            if await player.has_filter(i):
                await player.clear_filters(fast_apply=True)
                embed = Embed(title="Cleared up all the filters")
                embed.set_footer(text="May take 1-5 seconds")
                await inter.send(embed=embed)
                break
        else:
            raise NoFilterActive


def setup(bot: Vibr) -> None:
    bot.add_cog(ClearAll(bot))
