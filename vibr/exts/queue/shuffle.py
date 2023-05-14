from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter


class Shuffle(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def shuffle(self, inter: Inter) -> None:
        """Shuffle the songs in queue"""

        player = inter.guild.voice_client

        player.queue.shuffle()
        embed = Embed(title="Shuffled the queue")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Shuffle(bot))
