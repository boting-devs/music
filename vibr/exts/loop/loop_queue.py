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

class LoopQueue(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def loopqueue(self,inter:MyInter):
        """Loop the whole queue, going around in circles."""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client #pyright: ignore

        if not player.loop_queue_check:
            player.loop_queue_check = True
            player.loop_queue = [player.current]
            player.looped_user = inter.user.id
            embed = Embed(title="Looping Queue")
            await inter.send(embed=embed)
            
        else:
            player.loop_queue_check = False
            embed = Embed(title="Looping Queue Disabled")
            await inter.send(embed=embed)

def setup(bot: Vibr) -> None:
    bot.add_cog(LoopQueue(bot))