from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from botbase import CogBase
from mafic import EndReason, TrackEndEvent, TrackStartEvent

from vibr.bot import Vibr
from vibr.track_embed import track_embed
from vibr.embed import Embed
if TYPE_CHECKING:
    from vibr.player import Player

log = getLogger(__name__)


class Queue(CogBase[Vibr]):
    @CogBase.listener()
    async def on_track_end(self, event: TrackEndEvent[Player]) -> None:
        player = event.player

        if event.reason in (EndReason.FINISHED, EndReason.LOAD_FAILED):
            if player.loop_track:
                await player.play(player.loop_track)
                embed = await track_embed(
                    player.loop_track, bot=self.bot, loop=True, user=player.looped_user
                )
                if channel := player.notification_channel:
                    await channel.send(embed=embed)

            if player.loop_queue_check:
                user = player.looped_user
                player.queue += [(t, user) for t in player.loop_queue]
                log.info("player %s", player.loop_queue)

            log.info("Queue : %s", player.queue)
            try:
                play_next, member = player.queue.take()
            except IndexError:
                if channel := player.notification_channel:
                    embed = Embed(title="End of Queue")
                    await channel.send(embed=embed)
            else:
                await player.play(play_next)
                embed = await track_embed(play_next, bot=self.bot, user=member)
                if channel := player.notification_channel:
                    await channel.send(embed=embed)

    @CogBase.listener()
    async def on_track_start(self, event: TrackStartEvent[Player]) -> None:
        player = event.player

        if player.loop_queue_check and player.current is not None:
            player.loop_queue = [player.current]


def setup(bot: Vibr) -> None:
    bot.add_cog(Queue(bot))
