from __future__ import annotations

from asyncio import sleep
from typing import TYPE_CHECKING, cast

from botbase import CogBase
from nextcord.abc import Snowflake

from vibr.bot import Vibr
from vibr.player import Player

if TYPE_CHECKING:
    from nextcord import Member, VoiceState


class AutoDisconnect(CogBase[Vibr]):
    async def handle_own_voice_state(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        guild = member.guild
        # If we do not have a player, ignore this.
        if (player := guild.voice_client) is None:
            return

        player = cast(Player, player)

        # In case somehow cleanup didn't happen.
        if not after.channel and (player in player.node.players):
            await player.destroy()
            return

        # They moved us, pause for a second then continue.
        if player.current is not None and before.channel != after.channel:
            paused = player.paused
            await player.pause()
            await sleep(1)
            await player.pause(paused)
            return

    @CogBase.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        assert self.bot.user is not None

        if member.id == self.bot.user.id:
            await self.handle_own_voice_state(member, before, after)
            return

        # Joined, cancel existing timers.
        if before.channel is None and after.channel is not None:
            player = cast(Player | None, member.guild.voice_client)
            if (
                player is not None
                and cast(Snowflake, player.channel).id == after.channel.id
            ):
                player.cancel_pause_timer()

        # Left, start a timer if needed.
        elif before.channel is not None and after.channel is None:
            player = cast(Player | None, member.guild.voice_client)
            if (
                player is not None
                and len(before.channel.voice_states) == 1
                and cast(Snowflake, player.channel).id == before.channel.id
            ):
                player.start_pause_timer()

        # Switched channels, cancel existing timers.
        elif before.channel is not None and after.channel is not None:
            player = cast(Player | None, member.guild.voice_client)
            if player is not None:
                if cast(Snowflake, player.channel).id == before.channel.id:
                    player.start_pause_timer()
                elif cast(Snowflake, player.channel).id == after.channel.id:
                    player.cancel_pause_timer()


def setup(bot: Vibr) -> None:
    bot.add_cog(AutoDisconnect(bot))
