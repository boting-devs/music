from __future__ import annotations

from asyncio import sleep
from logging import getLogger
from typing import TYPE_CHECKING

from botbase import MyInter
from nextcord import Embed
from nextcord.ext.commands import Cog
from nextcord.utils import get

from .extras.playing_embed import playing_embed
from .extras.types import Player

if TYPE_CHECKING:
    from nextcord import Guild, Member, VoiceState
    from pomice import Track

    from ..__main__ import Vibr


log = getLogger(__name__)


class Events(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot

    @Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        # This is Vibr
        if member.id == self.bot.user.id:  # type: ignore
            guild = member.guild
            # If we do not have a player, ignore this.
            if (player := self.bot.pool.get_node().get_player(guild.id)) is None:
                return

            if not after.channel and not player.is_dead:
                return await player.destroy()

            # They moved us, pause for a second then continue.
            if player.is_playing and before.channel != after.channel:
                paused = player.is_paused
                await player.set_pause(True)
                await sleep(1)
                await player.set_pause(paused)

        else:
            # Someone joined, add them to cache
            if not before.channel and after.channel and not member.bot:
                if after.channel.id not in self.bot.listeners:
                    self.bot.listeners[after.channel.id] = {member.id}
                else:
                    self.bot.listeners[after.channel.id].add(member.id)

                log.info(
                    "Added %d to listener cache for %d", member.id, after.channel.id
                )

                # They joined, don't auto leave.
                if player := member.guild.voice_client:
                    assert isinstance(player, Player)
                    player.cancel_pause_timer()
            # Someone left, remove them from cache
            elif before.channel and not after.channel:
                if before.channel.id in self.bot.listeners:
                    self.bot.listeners.get(before.channel.id, set()).discard(member.id)
                    if not self.bot.listeners.get(before.channel.id, {1}):
                        del self.bot.listeners[before.channel.id]

                    log.info(
                        "Removed %d from listener cache for %d",
                        member.id,
                        before.channel.id,
                    )

                if len(self.bot.listeners.get(before.channel.id, set())) == 0 and (
                    player := member.guild.voice_client
                ):
                    assert isinstance(player, Player)
                    player.invoke_pause_timer()
            # They moved, move the cache of them too.
            elif (
                before.channel
                and after.channel
                and before.channel.id != after.channel.id
            ):
                if before.channel.id in self.bot.listeners:
                    self.bot.listeners.get(before.channel.id, set()).discard(member.id)
                    if not self.bot.listeners.get(before.channel.id, {1}):
                        del self.bot.listeners[before.channel.id]

                    log.info(
                        "Removed %d from listener cache for %d",
                        member.id,
                        before.channel.id,
                    )

                if after.channel.id not in self.bot.listeners:
                    self.bot.listeners[after.channel.id] = {member.id}
                else:
                    self.bot.listeners[after.channel.id].add(member.id)

                log.info(
                    "Added %d to listener cache for %d", member.id, after.channel.id
                )

                if player := member.guild.voice_client:
                    assert isinstance(player, Player)

                    # They left the player channel, check if empty.
                    if (
                        before.channel.id == player.channel.id
                        and len(self.bot.listeners.get(before.channel.id, set())) == 0
                    ):
                        player.invoke_pause_timer()

                    # They joined the channel with the player, don't make it pause.
                    if after.channel.id == player.channel.id:
                        player.cancel_pause_timer()

    @Cog.listener()
    async def on_application_command_completion(self, inter: MyInter):
        if inter.user.id not in self.bot.notified_users:
            row = await self.bot.db.fetchrow(
                "SELECT notified, notifications FROM users WHERE id=$1", inter.user.id
            )

            # They were not notified, notify them.
            if not row or (row["notifications"] and not row["notified"]):
                latest = await self.bot.db.fetchrow(
                    """SELECT * FROM notifications WHERE expiry > CURRENT_TIMESTAMP
                    ORDER BY id DESC LIMIT 1"""
                )

                if latest:
                    notifs_mention = self.bot.get_mention("notifications list")

                    await inter.send(
                        f"{inter.user.mention} You have a new notification "
                        f"with the title **{latest['title']}** "
                        f"from `{latest['datetime'].strftime('%y-%m-%d')}`. "
                        f"You can view all notifications with {notifs_mention}.",
                    )
                    log.debug("Sent notification to %d", inter.user.id)

                await self.bot.db.execute(
                    """INSERT INTO users (id, notified)
                    VALUES ($1, $2)
                    ON CONFLICT (id) DO UPDATE
                        SET notified = $2""",
                    inter.user.id,
                    True,
                )
                log.debug("Set notified to True for %d", inter.user.id)

            # They were either notified before or they have now.
            self.bot.notified_users.add(inter.user.id)

    async def play_next(self, player: Player):
        toplay = player.queue.pop(0)

        try:
            await player.play(toplay)
        except Exception as e:
            embed = Embed(
                title="Error when playing queued track",
                description=f"{e}\nAttempting to play next track...",
            )
            if toplay.ctx:
                channel = (
                    toplay.ctx.channel
                )  # pyright: ignore[reportOptionalMemberAccess]
                if channel.permissions_for(  # type: ignore
                    channel.guild.me  # type: ignore
                ).send_messages:
                    await channel.send(embed=embed)

            await self.on_pomice_track_end(player, toplay, "")
        else:
            inter = toplay.ctx
            if inter is None or inter.guild is None:
                return  # ???

            perms = inter.channel.permissions_for(inter.guild.me)  # type: ignore
            if (
                perms.view_channel
                and perms.send_messages
                and inter.guild.me.communication_disabled_until is None
            ):
                await playing_embed(toplay)

    @Cog.listener()
    async def on_pomice_track_end(self, player: Player, track: Track, __: str):
        await sleep(0.1)
        if player.is_playing:
            return

        if player.looped_track:
            await player.play(player.looped_track)
            await playing_embed(player.looped_track, loop=True)
            return

        if player.looped_queue_check:
            player.queue += player.loop_queue

        if player.queue:
            await self.play_next(player)
        else:
            player.track_end(track)

    @Cog.listener()
    async def on_guild_available(self, guild: Guild):
        # Hacky, but this gets the first voice states when we know about a guild.
        # This stores the initial states in cache.
        for m, vs in guild._voice_states.items():
            if vs.channel:
                log.info("Adding voice states for guild %d", guild.id)
                if vs.channel.id not in self.bot.listeners:
                    self.bot.listeners[vs.channel.id] = {m}
                else:
                    self.bot.listeners[vs.channel.id].add(m)


def setup(bot: Vibr) -> None:
    bot.add_cog(Events(bot))
