from __future__ import annotations

from typing import TYPE_CHECKING
from logging import getLogger

from botbase import CogBase, MyInter
from nextcord import slash_command
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from ._errors import EmptyQueue

if TYPE_CHECKING:
    from vibr.player import Player
log = getLogger(__name__)

class Clearqueue(CogBase[Vibr]):
    @slash_command(name="clear-queue",dm_permission=False)
    @is_connected_and_playing
    async def clearqueue(self,inter:MyInter) -> None:
        """Clear the queue keeping the current song playing."""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        if not player.queue:
            raise EmptyQueue
        else:
            player.queue.clear()
            embed = Embed(title="Cleared the queue")
            await inter.send(embed=embed)

def setup(bot: Vibr) -> None:
    bot.add_cog(Clearqueue(bot))