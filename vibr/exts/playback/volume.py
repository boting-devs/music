from __future__ import annotations

from typing import cast

from botbase import CogBase
from nextcord import SlashOption, slash_command
from nextcord.abc import Snowflake

from vibr.bot import Vibr
from vibr.checks import is_connected
from vibr.embed import Embed
from vibr.inter import Inter


class Volume(CogBase[Vibr]):
    VOLUME = SlashOption(min_value=1, max_value=500)

    @slash_command(dm_permission=False)
    @is_connected
    async def volume(self, inter: Inter, number: int = VOLUME) -> None:
        """Change volume of the current player.

        number:
            The volume to set, between 1 and 500, measured in % of normal.
        """

        player = inter.guild.voice_client

        await player.set_volume(number)
        embed = Embed(title=f"Volume set to {number}")
        await inter.send(embed=embed)

        # channel_id = cast(Snowflake, player.channel).id
        # config = await PlayerConfig.objects().get_or_create(
        #     PlayerConfig.channel_id == channel_id
        # )
        # config.volume = number
        # await config.save()


# volume cap left


def setup(bot: Vibr) -> None:
    bot.add_cog(Volume(bot))
