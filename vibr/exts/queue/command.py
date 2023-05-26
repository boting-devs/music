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

    @queue.subcommand()
    @is_connected_and_playing
    async def queue_move(self, inter: Inter, track: str, destination: int) -> None:
        """Move the song to a certain position in the queue.

        track:
            The number of the song to move, found via the queue.
        destination:
            The position to move the song to.
        """

        player: Player = inter.guild.voice_client

        assert inter.guild is not None and inter.guild.voice_client is not None

        if not player.queue:
            raise QueueEmpty

        length = len(player.queue)
        if destination < 1 or destination > length:
            raise IndexNotInRange

        if not track.isdigit():
            raise InvalidIndex

        track_index = int(track)

        track_n = player.queue[track_index - 1]
        player.queue.pop(track_index - 1)
        player.queue.insert(destination - 1, track_n, user=inter.user.id)

        embed = Embed(title=f'"{track_n.title}" position set to {destination}')
        await inter.send(embed=embed)

    @queue.subcommand(name="remove")
    @is_connected_and_playing
    async def queue_remove(self, inter: Inter, position: str) -> None:
        """Remove a selected song from the queue.

        position:
            The position of the song to remove, found via the queue.
        """

        player: Player = inter.guild.voice_client  # pyright: ignore

        assert inter.guild is not None and inter.guild.voice_client is not None

        if not player.queue:
            raise QueueEmpty

        if not position.isdigit():
            raise InvalidIndex

        position_index = int(position)
        length = len(player.queue)
        if position_index < 1 or position_index > length:
            raise IndexNotInRange

        try:
            song_n = player.queue[position_index - 1]
            player.queue.pop(position_index - 1)
        except IndexError:
            await inter.send(
                "Please input a number which is within your queue!", ephemeral=True
            )
            return

        await inter.send_author_embed(f'"{song_n.title}" removed from queue')

    @queue_move.on_autocomplete("track")
    @queue_remove.on_autocomplete("position")
    async def remove_autocomplete(self, inter: Inter, amount: str) -> dict[str, str]:
        player = inter.guild.voice_client

        if not player.queue:
            return {}

        if amount.isdigit():
            track_range = len(player.queue) - int(amount)
            numbers = (str(i + 1) for i in range(track_range))
            close_matches: list[str] = get_close_matches(
                amount, numbers, n=AUTOCOMPLETE_MAX, cutoff=0.05
            )

            tracks = [(i, player.queue[int(i)]) for i in close_matches]
            return {f"{i}: {get_str(track)}": i for i, track in tracks}

        if not amount:
            tracks = list(enumerate(player.queue.tracks))
            if len(tracks) > AUTOCOMPLETE_MAX:
                tracks = tracks[:AUTOCOMPLETE_MAX]

            return {f"{i+1}: {get_str(track)}": str(i + 1) for i, track in tracks}

        tracks = player.queue.tracks
        track_strings = map(get_str, tracks)
        close_matches = get_close_matches(
            amount, track_strings, n=AUTOCOMPLETE_MAX, cutoff=0.05
        )

        return {
            f"{i + 1}: {get_str(track)}": str(i + 1)
            for i, track in enumerate(tracks)
            if get_str(track) in close_matches
        }

    @queue.subcommand()
    @is_connected_and_playing
    async def queue_shuffle(self, inter: Inter) -> None:
        """Shuffle the songs in the queue"""

        player = inter.guild.voice_client

        player.queue.shuffle()
        embed = Embed(title="Shuffled the queue")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(QueueCommand(bot))
