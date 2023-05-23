from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.inter import Inter
from vibr.track_embed import track_embed


class Grab(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def grab(self, inter: Inter) -> None:
        """Sends the current playing song through direct messages"""

        player = inter.guild.voice_client
        embed, view = await track_embed(
            player.current, bot=self.bot, user=inter.user.id, inter=inter, grabbed=True
        )

        await inter.user.send(embed=embed)

        await inter.send("📬 Grabbed", ephemeral=True)


def setup(bot: Vibr) -> None:
    bot.add_cog(Grab(bot))
