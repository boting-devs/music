from __future__ import annotations

from logging import getLogger

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter

from ._errors import EmptyQueue
from ._views import QueueMenu, QueueSource

log = getLogger(__name__)


class QueueCommand(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    async def queue(self, inter: Inter) -> None:
        ...

    @queue.subcommand(name="clear")
    @is_connected_and_playing
    async def queue_clear(self, inter: Inter) -> None:
        """Clear the queue, keeping the current song playing."""

        player = inter.guild.voice_client

        if not player.queue:
            raise EmptyQueue

        player.queue.clear()
        embed = Embed(title="Cleared the queue")
        await inter.send(embed=embed)

    @queue.subcommand(name="list")
    @is_connected_and_playing
    async def queue_list(self, inter: Inter) -> None:
        """List all the tracks in the queue."""

        player = inter.guild.voice_client

        current = player.current
        assert current is not None
        queue = player.queue
        if not queue and not current:
            raise EmptyQueue

        menu = QueueMenu(source=QueueSource([current, *queue]), inter=inter)
        await menu.start(interaction=inter)


def setup(bot: Vibr) -> None:
    bot.add_cog(QueueCommand(bot))
