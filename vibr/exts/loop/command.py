from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter
from .loop_track import Looptrack
from .loop_queue import LoopQueue


class LoopCommand(CogBase[Vibr]):
    loop_track = Looptrack(Vibr)
    loop_queue = LoopQueue(Vibr)

    @slash_command(dm_permission=False)
    async def loop(self, inter: Inter) -> None:
        ...

    async def loop_track_command(self, inter: Inter) -> None:
        await self.loop_track.looptrack(inter)

    async def loop_queue_command(self, inter: Inter) -> None:
        await self.loop_queue.loopqueue(inter)

    @loop.subcommand(name="track")
    @is_connected_and_playing
    async def _looptrack(self, inter: Inter) -> None:
        """Loop the current track again, and again, and again."""
        await self.loop_track_command(inter)

    @loop.subcommand(name="queue")
    @is_connected_and_playing
    async def _loopqueue(self, inter: Inter) -> None:
        """Loop the whole queue, going around in circles."""
        await self.loop_queue_command(inter)


def setup(bot: Vibr) -> None:
    bot.add_cog(LoopCommand(bot))
