from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

from ._errors import AlreadyResumed

if TYPE_CHECKING:
    from vibr.player import Player


class Resume(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def resume(self, inter: MyInter) -> None:
        """Resume your beats."""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        if player.paused is True:
            await player.resume()
            embed = Embed(
                title="Resumed",
                timestamp=utcnow(),
            )
            await inter.send(embed=embed)
        else:
            raise AlreadyResumed


def setup(bot: Vibr) -> None:
    bot.add_cog(Resume(bot))
