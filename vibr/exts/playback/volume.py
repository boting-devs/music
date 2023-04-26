from __future__ import annotations

from typing import TYPE_CHECKING, cast

from botbase import CogBase, MyInter
from nextcord import slash_command
from nextcord.abc import Snowflake
from nextcord.utils import utcnow
from ormar import NoMatch

from vibr.bot import Vibr
from vibr.checks import is_connected
from vibr.db.player import PlayerConfig
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player


class Volume(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def volume(self, inter: MyInter, number: int) -> None:
        """Change volume of the current player.

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

        channel_id = cast(Snowflake, player.channel).id
        try:
            model = await PlayerConfig.objects.get(channel_id=channel_id)
        except NoMatch:
            await PlayerConfig.objects.create(channel_id=channel_id, volume=number)
        else:
            await model.update(volume=number)


# volume cap left


def setup(bot: Vibr) -> None:
    bot.add_cog(Volume(bot))
