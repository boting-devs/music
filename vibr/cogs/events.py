from __future__ import annotations

from asyncio import sleep
from typing import TYPE_CHECKING

from botbase import MyContext
from nextcord import Embed
from nextcord.ext.commands import Cog

if TYPE_CHECKING:
    from nextcord import Guild, Member, VoiceState

    from ..__main__ import Vibr

    Context = MyContext[Vibr]


slash_description = (
    "As Discord is forcing [slash commands]"
    "(<https://support.discord.com/hc/en-us/articles/1500000368501-Slash-Commands-FAQ>) "
    "by the 31st of August, Vibr has to do the same. This message is to let you know "
    "that slash commands will not work past the 31st of August, so you will need to start "
    "using slash commands sooner rather than later. If somehow the slash commands do not show, "
    "check with a moderator of this server to see if everyone has the "
    "`Use Application Commands` permission in the preferred commands channel. "
    "If that still does not work, you can reinvite vibr (no need to kick) with "
    "[this link](https://discord.com/oauth2/authorize?client_id=882491278581977179&permissions=3427392&scope=bot%20applications.commands)"
)


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
    async def on_command_completion(self, ctx: Context):
        if not await self.bot.is_owner(ctx.author):  # type: ignore
            await ctx.send_embed(
                title="Prefix Commands Will Stop Working Soon",
                desc=slash_description,
            )


def setup(bot: Vibr) -> None:
    bot.add_cog(Events(bot))
