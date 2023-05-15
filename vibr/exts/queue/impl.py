from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from botbase import CogBase
from mafic import EndReason, TrackEndEvent, TrackStartEvent

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.track_embed import track_embed

if TYPE_CHECKING:
    from vibr.player import Player

log = getLogger(__name__)


class Queue(CogBase[Vibr]):
    @CogBase.listener()
    async def on_track_end(self, event: TrackEndEvent[Player]) -> None:
        player = event.player

        if event.reason in (EndReason.FINISHED, EndReason.LOAD_FAILED):
            try:
                play_next, member = player.queue.take()
            except IndexError:
                if channel := player.notification_channel:
                    embed = Embed(title="End of Queue")
                    await channel.send(embed=embed)
                    player.start_disconnect_timer()
            else:
                await player.play(play_next)
                if player.dnd:
                    return

                embed = await track_embed(
                    play_next,
                    bot=self.bot,
                    user=member,
                    looping=player.queue.loop_type is not None,
                )
                if channel := player.notification_channel:
                    await channel.send(embed=embed)

    @CogBase.listener()
    async def on_track_start(self, event: TrackStartEvent[Player]) -> None:
        player = event.player

        if player.loop_queue_check and player.current is not None:
            player.loop_queue = [player.current]


def setup(bot: Vibr) -> None:
    bot.add_cog(Queue(bot))
