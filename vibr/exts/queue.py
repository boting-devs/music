from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase
from mafic import EndReason, TrackEndEvent , TrackStartEvent 
from logging import getLogger

from vibr.bot import Vibr
from vibr.track_embed import track_embed

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
                h = (player.loop_queue,player.looped_user)
                player.queue.extend(h)
                log.info(f"player %s",player.loop_queue)
                
            log.info(f"Queue : %s",player.queue)
            try:
                play_next, member = player.queue.take()
            except IndexError:
                pass
            else:
                await player.play(play_next)
                embed = await track_embed(play_next, bot=self.bot, user=member)
                if channel := player.notification_channel:
                    await channel.send(embed=embed)

    @CogBase.listener()
    async def on_track_start(self,event:TrackStartEvent[Player]) -> None:
        player = event.player

        if player.loop_queue_check:
            player.loop_queue = [player.current]


def setup(bot: Vibr) -> None:
    bot.add_cog(Queue(bot))
