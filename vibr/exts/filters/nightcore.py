from __future__ import annotations

from logging import getLogger

from botbase import CogBase
from mafic import Filter, Timescale
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter

log = getLogger(__name__)


class Nightcore(CogBase[Vibr]):
    @slash_command(name="nightcore", dm_permission=False)
    @is_connected_and_playing
    async def nightcore(self, inter: Inter) -> None:
        """A funny filter. Just try it out!"""

        player = inter.guild.voice_client

        if await player.has_filter("nightcore"):
            await player.remove_filter("nightcore", fast_apply=True)
            embed = Embed(title="Nightcore Filter Deactivated")
            log.info("Disabled nightcore", extra={"guild": inter.guild.id})
        else:
            night = Timescale(speed=1.25, pitch=1.3)
            nightcore_filter = Filter(timescale=night)
            await player.add_filter(
                nightcore_filter, label="nightcore", fast_apply=True
            )
            embed = Embed(title="Nightcore Filter activated")
            log.info("Enabled nightcore", extra={"guild": inter.guild.id})

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Nightcore(bot))
