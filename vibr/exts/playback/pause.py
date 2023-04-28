from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter

from ._errors import AlreadyPaused


class Pause(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def pause(self, inter: Inter) -> None:
        """Pause your beats."""

        player = inter.guild.voice_client

        if player._paused is False:
            await player.pause(pause=True)
            embed = Embed(
                title="Paused",
                timestamp=utcnow(),
            )
            await inter.send(embed=embed)
        else:
            raise AlreadyPaused


def setup(bot: Vibr) -> None:
    bot.add_cog(Pause(bot))
