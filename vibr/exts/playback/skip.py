from __future__ import annotations

from difflib import get_close_matches
from typing import TYPE_CHECKING

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected
from vibr.track_embed import track_embed
from vibr.utils import truncate

from ..playing._errors import AmountNotInt, IndexNotInQueue, QueueEmpty

if TYPE_CHECKING:
    from mafic import Track

    from vibr.inter import Inter


AUTOCOMPLETE_MAX = 25


def get_str(track: Track) -> str:
    return truncate(f"{track.title} by {track.author}", length=90)


class Skip(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def skip(self, inter: Inter, amount: str | None = None) -> None:
        """Skip the currently playing song, and optionally extra songs.

        amount:
            The amount of songs to remove, including the currently playing one.
            Leave blank to only skip the current song.
        """

        player = inter.guild.voice_client

        if amount:
            if not amount.isdigit():
                raise AmountNotInt

            amount_int = int(amount)
        else:
            amount_int = 1

        if not player.queue:
            raise QueueEmpty

        if amount_int > len(player.queue):
            raise IndexNotInQueue

        track, user = player.queue.skip(amount_int)
        await player.play(track)
        embed = await track_embed(track, user=user, skipped=inter.user.id, bot=self.bot)
        await inter.response.send_message(embed=embed)

    @skip.on_autocomplete("amount")
    async def skip_autocomplete(self, inter: Inter, amount: str) -> dict[str, str]:
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
    bot.add_cog(Skip(bot))
