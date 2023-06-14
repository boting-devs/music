from __future__ import annotations

from difflib import get_close_matches
from logging import getLogger
from typing import TYPE_CHECKING

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter
from vibr.utils import truncate

from ..playing._errors import QueueEmpty
from ._errors import EmptyQueue, IndexNotInRange, InvalidIndex
from ._views import QueueMenu, QueueSource

if TYPE_CHECKING:
    from mafic import Track

    from vibr.player import Player


AUTOCOMPLETE_MAX = 25
log = getLogger(__name__)


def get_str(track: Track) -> str:
    return truncate(f"{track.title} by {track.author}", length=90)


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

    @queue.subcommand(name="shuffle")
    @is_connected_and_playing
    async def queue_shuffle(self, inter: Inter) -> None:
        """Shuffle the songs in the queue"""

        player = inter.guild.voice_client

        player.queue.shuffle()
        embed = Embed(title="Shuffled the queue")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(QueueCommand(bot))
