from __future__ import annotations

from datetime import UTC, datetime
from time import gmtime, strftime

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter

from ._errors import InvalidFormat, NotInRange


class Seek(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def seek(self, inter: Inter, timestamp: str) -> None:
        """Seek song to a particular timestamp.

        timestamp:
            The time to seek to, in SS, MM:SS or HH:MM:SS format.
        """

        player = inter.guild.voice_client

        assert player.current is not None

        try:
            b = datetime.strptime(timestamp, "%H:%M:%S").astimezone(UTC)
        except ValueError:
            try:
                b = datetime.strptime(timestamp, "%M:%S").astimezone(UTC)
            except ValueError as e:
                raise InvalidFormat from e

        seektime = (b.second + b.minute * 60 + b.hour * 3600) * 1000

        if player.current.length < seektime:
            raise NotInRange

        await player.seek(seektime)
        current = strftime("%H:%M:%S", gmtime(seektime // 1000))
        embed = Embed(title=f"Position seeked to {current}")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Seek(bot))
