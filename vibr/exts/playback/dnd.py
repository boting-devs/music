from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected
from vibr.embed import Embed
from vibr.inter import Inter


class Dnd(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def dnd(self, inter: Inter) -> None:
        """Disable sending embeds at the start of every song."""

        player = inter.guild.voice_client
        if not player.dnd:
            player.dnd = True
            embed = Embed(
                title="DND mode ON",
                description="Now the bot wont send an embed at the start of every song",
            )
        else:
            player.dnd = False
            embed = Embed(
                title="DND mode OFF",
                description="Now the bot will send an embed at the start of every song",
            )

        embed.set_footer(icon_url=inter.author.display_avatar.url)
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Dnd(bot))
