from __future__ import annotations

from botbase import CogBase
from mafic import Filter, Timescale
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter
from ._error import InvalidSpeed, SpeedNotActive


class Speed(CogBase[Vibr]):
    @slash_command(name="speed", dm_permission=False)
    @is_connected_and_playing
    async def speed(self, inter: Inter, speed: float | None) -> None:
        """Increase/Decrease Speed of the song
        speed:
            Accepted Range : 0 - 2. Use 1 for normal speed or leave it blank."""

        player = inter.guild.voice_client

        if speed is None and not await player.has_filter("speed"):
            raise SpeedNotActive

        if speed is not None:
            if speed > 2 or speed <= 0:
                raise InvalidSpeed

        if await player.has_filter("speed") and speed is not None and speed != 1:
            await player.remove_filter("speed", fast_apply=True)
            speed_filter = Timescale(speed=speed)
            speed_filter_object = Filter(timescale=speed_filter)
            await player.add_filter(speed_filter_object, label="speed", fast_apply=True)
            embed = Embed(title=f"Speed switched to {speed}x")

        elif await player.has_filter("speed") or speed == 1:
            await player.remove_filter("speed", fast_apply=True)
            embed = Embed(title="Speed switched to normal")

        else:
            speed_filter = Timescale(speed=speed)
            speed_filter_object = Filter(timescale=speed_filter)
            await player.add_filter(speed_filter_object, label="speed", fast_apply=True)
            embed = Embed(title=f"Speed switched to {speed}x")

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Speed(bot))
