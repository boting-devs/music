from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player


class Volume(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def volume(self, inter: MyInter, number: int) -> None:
        """Change Player's Volume

        number:
        The volume to set, between 1 and 500, measured in % of normal.
        """

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        await player.set_volume(number)
        embed = Embed(
            title=f"Volume set to {number}",
            description=inter.user.mention,
            timestamp=utcnow(),
        )
        await inter.send(embed=embed)


# volume cap left
# volume save per vc also left(need to connect to db)


def setup(bot: Vibr) -> None:
    bot.add_cog(Volume(bot))
