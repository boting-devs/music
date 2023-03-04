from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase
from mafic import EndReason, TrackEndEvent

from vibr.bot import Vibr
from vibr.track_embed import track_embed

if TYPE_CHECKING:
    from vibr.player import Player


class Queue(CogBase[Vibr]):
    @CogBase.listener()
    async def on_track_end(self, event: TrackEndEvent[Player]) -> None:
        player = event.player

        if event.reason in (EndReason.FINISHED, EndReason.LOAD_FAILED):
            try:
                play_next, member = player.queue.take()
            except IndexError:
                pass
            else:
                await player.play(play_next)
                embed = await track_embed(play_next, bot=self.bot, user=member)
                if channel := player.notification_channel:
                    await channel.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Queue(bot))
