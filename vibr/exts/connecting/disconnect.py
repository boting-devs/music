from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter

from ...checks import is_connected
from ._errors import UserNotInVoice


class Disconnect(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def disconnect(self, inter: Inter) -> None:
        """Bye bye :("""

        player = inter.guild.voice_client

        await player.destroy()
        embed = Embed(title="Bye :(")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Disconnect(bot))
