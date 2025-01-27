from __future__ import annotations

from difflib import get_close_matches
from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.inter import Inter
from vibr.utils import truncate

from ..playing._errors import QueueEmpty
from ._errors import IndexNotInRange, InvalidIndex

if TYPE_CHECKING:
    from mafic import Track

    from vibr.player import Player


AUTOCOMPLETE_MAX = 25


def get_str(track: Track) -> str:
    return truncate(f"{track.title} by {track.author}", length=90)


class Remove(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def remove(self, inter: MyInter, position: str) -> None:
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

        await inter.send_embed(
            title=f'"{song_n.title}" removed from queue',
            cmd_invoker=False
        )

    @remove.on_autocomplete("position")
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


def setup(bot: Vibr) -> None:
    bot.add_cog(Remove(bot))
