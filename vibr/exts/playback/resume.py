from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter

from ._errors import AlreadyResumed


class Resume(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def resume(self, inter: Inter) -> None:
        """Resume your beats."""

        player = inter.guild.voice_client

        if player.paused is True:
            await player.resume()
            embed = Embed(title="Resumed")
            await inter.send(embed=embed)
        else:
            raise AlreadyResumed


def setup(bot: Vibr) -> None:
    bot.add_cog(Resume(bot))
