from __future__ import annotations

from logging import getLogger

from botbase import CogBase
from mafic import Filter, Timescale
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing, voted
from vibr.embed import Embed
from vibr.inter import Inter

from ._error import InvalidSpeed, SpeedNotActive

log = getLogger(__name__)
MAX_SPEED = 2


class Speed(CogBase[Vibr]):
    @slash_command(name="speed", dm_permission=False)
    @is_connected_and_playing
    @voted
    async def speed(self, inter: Inter, speed: float | None) -> None:
        """Increase/Decrease Speed of the song

        speed:
            Accepted Range: 0.1 - 2. Use 1 for normal speed or leave it blank.
        """

        player = inter.guild.voice_client

        if speed is None and not await player.has_filter("speed"):
            raise SpeedNotActive

        if speed is not None and (speed > MAX_SPEED or speed <= 0.1):
            raise InvalidSpeed
        
        if not await player.has_filter("speed") and speed ==1:
            raise InvalidSpeed

        if await player.has_filter("speed") and speed is not None and speed != 1:
            await player.remove_filter("speed", fast_apply=True)
            speed_filter = Timescale(speed=speed)
            speed_filter_object = Filter(timescale=speed_filter)
            await player.add_filter(speed_filter_object, label="speed", fast_apply=True)
            embed = Embed(title=f"Speed switched to {speed}x")
            log.info("Changed speed to %d", speed, extra={"guild": inter.guild.id})
        
        elif await player.has_filter("speed") or speed == 1:
            await player.remove_filter("speed", fast_apply=True)
            embed = Embed(title="Speed switched to normal")
            log.info("Changed speed to normal", extra={"guild": inter.guild.id})
        else:
            speed_filter = Timescale(speed=speed)
            speed_filter_object = Filter(timescale=speed_filter)
            await player.add_filter(speed_filter_object, label="speed", fast_apply=True)
            embed = Embed(title=f"Speed switched to {speed}x")
            log.info("Changed speed to %d", speed, extra={"guild": inter.guild.id})

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Speed(bot))
