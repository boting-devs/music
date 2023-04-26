from __future__ import annotations

from datetime import UTC, datetime
from time import gmtime, strftime
from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

from ._errors import InvalidFormat, NotInRange

if TYPE_CHECKING:
    from vibr.player import Player


class Seek(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def seek(self, inter: MyInter, timestamp: str) -> None:
        """Seek song to a particular timestamp.

        timestamp:
            The time to seek to, in SS, MM:SS or HH:MM:SS format.
        """

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

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
