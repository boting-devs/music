from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter


class LoopQueue(CogBase[Vibr]):
    async def loopqueue(self, inter: Inter) -> None:
        """Loop the whole queue, going around in circles."""

        player = inter.guild.voice_client

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
