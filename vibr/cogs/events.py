from __future__ import annotations

from asyncio import sleep, TimeoutError as AsyncTimeoutError
from typing import TYPE_CHECKING
from logging import getLogger

from botbase import MyInter
from nextcord.ext.commands import Cog

if TYPE_CHECKING:
    from nextcord import Guild, Member, VoiceState

    from ..__main__ import Vibr


log = getLogger(__name__)


class Events(Cog):
    def __init__(self, bot: Vibr):
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
        elif not member.bot:
            if not before.channel and after.channel:
                if after.channel.id not in self.bot.listeners:
                    self.bot.listeners[after.channel.id] = {member.id}
                else:
                    self.bot.listeners[after.channel.id].add(member.id)

                if task := self.bot.listener_tasks.get(member.guild.id):
                    task.cancel()
                    del self.bot.listener_tasks[member.guild.id]
            elif before.channel and not after.channel:
                if before.channel.id in self.bot.listeners:
                    self.bot.listeners.get(before.channel.id, set()).discard(member.id)
                    if not self.bot.listeners.get(before.channel.id, {1}):
                        del self.bot.listeners[before.channel.id]

    @Cog.listener()
    async def on_guild_available(self, guild: Guild):
        for m, vs in guild._voice_states.items():
            if vs.channel:
                if vs.channel.id not in self.bot.listeners:
                    self.bot.listeners[vs.channel.id] = {m}
                else:
                    self.bot.listeners[vs.channel.id].add(m)

    @Cog.listener()
    async def on_application_command_completion(self, inter: MyInter):
        if inter.user.id not in self.bot.notified_users:
            is_notified = await self.bot.db.fetchval(
                "SELECT notified FROM users WHERE id=$1", inter.user.id
            )

            if not is_notified:
                latest = await self.bot.db.fetchrow(
                    "SELECT * FROM notifications ORDER BY id DESC LIMIT 1"
                )

                if latest:
                    await inter.send(
                        f"{inter.user.mention} You have a new notification with the title "
                        f"**{latest['title']}** "
                        f"from `{latest['datetime'].strftime('%y-%m-%d')}`. "
                        "You can view all notifications with </notifications:1004841251549478992>."
                    )

                await self.bot.db.execute(
                    """INSERT INTO users (id, notified)
                    VALUES ($1, $2)
                    ON CONFLICT (id) DO UPDATE
                        SET notified = $2""",
                    inter.user.id,
                    True,
                )

            self.bot.notified_users.add(inter.user.id)


def setup(bot: Vibr) -> None:
    bot.add_cog(Events(bot))
