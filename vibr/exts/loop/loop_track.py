from __future__ import annotations

from botbase import CogBase
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter


class Looptrack(CogBase[Vibr]):
    async def looptrack(self, inter: Inter) -> None:
        """Loop the current track again, and again, and again."""

        player = inter.guild.voice_client

        if not player.loop_track:
            player.loop_track = player.current
            player.looped_user = inter.user.id
            embed = Embed(
                title="Loop Mode On",
                description=f"{inter.user.mention} turned on loop mode",
                timestamp=utcnow(),
            )
            await inter.send(embed=embed)

        else:
            player.loop_track = None
            embed = Embed(
                title="Loop Mode Off",
                description=f"{inter.user.mention} turned off loop mode",
                timestamp=utcnow(),
            )


def setup(bot: Vibr) -> None:
    bot.add_cog(Looptrack(bot))
