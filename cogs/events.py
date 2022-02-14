from __future__ import annotations

from typing import TYPE_CHECKING
from asyncio import sleep

from nextcord.ext.commands import Cog

if TYPE_CHECKING:
    from nextcord import VoiceState, Member

    from ..mmain import MyBot


class Events(Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        if member.id == self.bot.user.id:  # type: ignore
            guild = member.guild
            if (player := self.bot.pool.get_node().get_player(guild.id)) is None:
                return

            if not after.channel and not player.is_dead:
                return await player.destroy()

            if player.is_playing and before.channel != after.channel:
                paused = player.is_paused
                await player.set_pause(True)
                await sleep(1)
                await player.set_pause(paused)
        else:
            if not before.channel and after.channel:
                if after.channel.id not in self.bot.listeners:
                    self.bot.listeners[after.channel.id] = {member.id}
                else:
                    self.bot.listeners[after.channel.id].add(member.id)
            elif before.channel and not after.channel:
                if before.channel.id in self.bot.listeners:
                    self.bot.listeners.get(before.channel.id, set()).discard(member.id)
                    if not self.bot.listeners.get(before.channel.id, {1}):
                        del self.bot.listeners[before.channel.id]


def setup(bot: MyBot) -> None:
    bot.add_cog(Events(bot))
