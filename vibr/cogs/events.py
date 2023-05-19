from __future__ import annotations

from asyncio import sleep
from logging import getLogger
from typing import TYPE_CHECKING, cast

from botbase import CogBase
from nextcord import Embed
from nextcord.abc import Snowflake
from nextcord.ext.tasks import loop
from pomice import Track

from vibr.__main__ import Vibr
from vibr.cogs.extras.playing_embed import playing_embed

from .extras.types import MyInter, Player

if TYPE_CHECKING:
    from nextcord import Member, VoiceState


log = getLogger(__name__)


class Events(CogBase[Vibr]):
    def __init__(self, bot: Vibr):
        super().__init__(bot)

        self.fix_clients.start()

    @loop(seconds=15)
    async def fix_clients(self):
        for player in self.bot.voice_clients:
            if not player.is_connected:
                try:
                    await player.destroy()
                except Exception:
                    log.error("failed to clean player", exc_info=True)

    async def handle_own_voice_state(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        guild = member.guild
        # If we do not have a player, ignore this.
        if (player := guild.voice_client) is None:
            return

        player = cast(Player, player)

        # In case somehow cleanup didn't happen.
        if not after.channel and player.is_dead:
            await player.destroy()
            return

        # They moved us, pause for a second then continue.
        if player.current is not None and before.channel != after.channel:
            paused = player.is_paused
            await player.set_pause(True)
            await sleep(1)
            await player.set_pause(paused)
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
            log.info("Joined, player: %s", player)
            if (
                player is not None
                and cast(Snowflake, player.channel).id == after.channel.id
            ):
                log.info("Joined, cancelling timer")
                player.cancel_pause_timer()

        # Left, start a timer if needed.
        elif before.channel is not None and after.channel is None:
            player = cast(Player | None, member.guild.voice_client)
            if (
                player is not None
                and cast(Snowflake, player.channel).id == before.channel.id
                and len(before.channel.voice_states) == 1
            ):
                player.start_pause_timer()

        # Switched channels, cancel existing timers.
        elif (
            before.channel is not None
            and after.channel is not None
            and before.channel != after.channel
        ):
            player = cast(Player | None, member.guild.voice_client)
            if player is not None:
                if (
                    cast(Snowflake, player.channel).id == before.channel.id
                    and len(before.channel.voice_states) == 1
                ):
                    player.start_pause_timer()
                elif cast(Snowflake, player.channel).id == after.channel.id:
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

    @CogBase.listener()
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
            player.start_disconnect_timer()


def setup(bot: Vibr) -> None:
    bot.add_cog(Events(bot))
