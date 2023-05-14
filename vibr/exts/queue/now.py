from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.inter import Inter
from vibr.track_embed import track_embed


class Nowplaying(CogBase[Vibr]):
    @slash_command(dm_permission=False, name="now-playing")
    @is_connected_and_playing
    async def playing(self, inter: Inter) -> None:
        """Show current beats"""

        player = inter.guild.voice_client
        assert player.current is not None

        embed = await track_embed(
            player.current,
            bot=self.bot,
            user=inter.user.id,
            inter=inter,
            length_embed=True,
        )
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Nowplaying(bot))
