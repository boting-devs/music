from __future__ import annotations

from asyncio import sleep
from typing import TYPE_CHECKING

from botbase import MyContext, MyInter
from nextcord.ext.commands import Cog

if TYPE_CHECKING:
    from nextcord import Guild, Member, VoiceState

    from ..__main__ import Vibr

    Context = MyContext[Vibr]


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
        else:
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
        await self.on_command_completion(inter)

    @Cog.listener()
    async def on_command_completion(self, ctx: MyContext | MyInter):
        if ctx.author.id not in self.bot.notified_users:
            is_notified = await self.bot.db.fetchval(
                "SELECT notified FROM users WHERE id=$1", ctx.author.id
            )

            if not is_notified:
                latest = await self.bot.db.fetchrow(
                    "SELECT * FROM notifications ORDER BY id DESC LIMIT 1"
                )

                await ctx.send(
                    f"{ctx.author.mention} You have a new notification with the title "
                    f"**{latest['title']}** "
                    f"from `{latest['datetime'].strftime('%y-%m-%d')}`. "
                    "You can view all notifications with </notifications:1004841251549478992>."
                )

                await self.bot.db.execute(
                    """INSERT INTO users (id, notified)
                    VALUES ($1, $2)
                    ON CONFLICT (id) DO UPDATE
                        SET notified = $2""",
                    ctx.author.id,
                    True,
                )

            self.bot.notified_users.add(ctx.author.id)


def setup(bot: Vibr) -> None:
    bot.add_cog(Events(bot))
