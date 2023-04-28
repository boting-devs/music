from __future__ import annotations

from time import gmtime, strftime

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter

from ._errors import NotInRange


class Forward(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def forward(self, inter: Inter, seconds: int) -> None:
        """Seek forward in the current song by an amount.

        seconds:
            The amount to seek forward by in seconds.
        """

        player = inter.guild.voice_client

        assert player.current is not None

        c = player.position
        time_left = player.current.length - c
        # s -> ms
        amount = c + (seconds * 1000)
        if amount > time_left:
            raise NotInRange
        # Format the time into a human readable format.
        current = strftime("%H:%M:%S", gmtime(amount // 1000))
        await player.seek(amount)
        embed = Embed(title=f"Position seeked to {current}")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Forward(bot))
