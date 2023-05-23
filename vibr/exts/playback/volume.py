from __future__ import annotations

from typing import cast

from botbase import CogBase
from nextcord import slash_command
from nextcord.abc import Snowflake
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.checks import is_connected
from vibr.db.player import PlayerConfig
from vibr.embed import Embed
from vibr.inter import Inter


class Volume(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def volume(self, inter: Inter, number: int) -> None:
        """Change volume of the current player.

        number:
            The volume to set, between 1 and 500, measured in % of normal.
        """

        player = inter.guild.voice_client

        await player.set_volume(number)
        embed = Embed(
            title=f"Volume set to {number}",
            timestamp=utcnow(),
        )
        await inter.send(embed=embed)

        channel_id = cast(Snowflake, player.channel).id
        config = await PlayerConfig.objects().get_or_create(
            PlayerConfig.channel_id == channel_id
        )
        config.volume = number
        await config.save()


# volume cap left


def setup(bot: Vibr) -> None:
    bot.add_cog(Volume(bot))
