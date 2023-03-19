from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase, MyInter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected
from vibr.track_embed import track_embed

from ._errors import AmountAndToProvided, IndexNotInQueue, QueueEmpty, ToNotIndex

if TYPE_CHECKING:
    from vibr.player import Player


class Skip(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def skip(
        self, inter: MyInter, amount: int = 1, to: str | None = None
    ) -> None:
        """Skip the currently playing song, and optionally extra songs.

        amount:
            The amount of songs to remove, including the currently playing one.
            Leave blank to only skip the current song. This should not be used alongside
            `to`.
        to:
            The song to skip up until. Leave blank to skip to the next song.
            This should not be used alongside `amount`.
        """

        assert inter.guild is not None and inter.guild.voice_client is not None

        if amount != 1 and to:
            raise AmountAndToProvided

        player: Player = inter.guild.voice_client  # pyright: ignore

        if to:
            if not to.isdigit():
                raise ToNotIndex

            amount = int(to)

        if not player.queue:
            raise QueueEmpty

        if amount > len(player.queue):
            raise IndexNotInQueue

        track, user = player.queue.skip(amount)
        await player.play(track)
        embed = await track_embed(track, user=user, skipped=inter.user.id, bot=self.bot)
        await inter.response.send_message(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Skip(bot))
