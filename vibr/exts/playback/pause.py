from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command
from nextcord.utils import utcnow
from vibr.bot import Vibr
from vibr.checks import is_connected

from vibr.embed import Embed
from ._errors import AlreadyPaused

if TYPE_CHECKING:
    from mafic import Track

    from vibr.player import Player

class Pause(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def pause(self,inter:MyInter):
        """Pause your beats"""

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore
        
        if player._paused == False:
            await player.pause(pause=True)
            embed = Embed(title="Paused",description=f"{inter.user.mention} paused.",timestamp=utcnow())
            await inter.send(embed=embed)
        else:
            raise AlreadyPaused

def setup(bot: Vibr) -> None:
    bot.add_cog(Pause(bot))