from __future__ import annotations

from time import gmtime, strftime
from typing import TYPE_CHECKING , cast

from difflib import get_close_matches

from botbase import CogBase, MyInter
from nextcord import slash_command , Range

from collections import deque

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter
from vibr.utils import truncate

from logging import getLogger


from ..playing._errors import QueueEmpty


if TYPE_CHECKING:
    from vibr.player import Player
    from mafic import Track


AUTOCOMPLETE_MAX = 25

def get_str(track: Track) -> str:
    return truncate(f"{track.title} by {track.author}", length=90)

log = getLogger(__name__)


class Move(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected_and_playing
    async def move(self,inter:Inter,track:str,destination:int) -> None:
        """Move the song to a certain position in your queue.

        track:
            The number of the song to move, found via the queue.
        destination:
            The position to move the song to."""
        
        player: Player = inter.guild.voice_client  # pyright: ignore

        assert inter.guild is not None and inter.guild.voice_client is not None

        if not player.queue:
            raise QueueEmpty
        
        track_index = int(track)

        try:
            track_n = player.queue[track_index-1]
            player.queue.pop(track_index-1)

        except IndexError:
            return await inter.send(
                "Please input a number which is within your queue!", ephemeral=True
            )
        dest_index = player.queue.index(track_n)
        player.queue.insert(destination-1,track_n,user=inter.user.id)
        embed = Embed(title=f"\"{track_n.title}\" position set to {dest_index}")
        await inter.send(embed=embed)

    @move.on_autocomplete("track")
    async def remove_autocomplete(self, inter:Inter, amount: str) -> dict[str, str]:
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
    bot.add_cog(Move(bot))