from __future__ import annotations

from asyncio import sleep
from logging import getLogger
from typing import TYPE_CHECKING

from botbase import MyInter
from nextcord.ext.commands import Cog
from nextcord.utils import get

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

    @Cog.listener()
    async def on_application_command_completion(self, inter: MyInter):
        if inter.user.id not in self.bot.notified_users:
            is_notified = await self.bot.db.fetchval(
                "SELECT notified FROM users WHERE id=$1", inter.user.id
            )

            # They were not notified, notify them.
            if not is_notified:
                latest = await self.bot.db.fetchrow(
                    "SELECT * FROM notifications ORDER BY id DESC LIMIT 1"
                )

                if latest:
                    notifs_command = get(
                        self.bot.get_all_application_commands(), name="notifications"
                    )
                    notifs_mention = (
                        notifs_command.get_mention()  # type: ignore[member-access]
                        if notifs_command
                        else "`/notifications`"
                    )

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


def setup(bot: Vibr) -> None:
    bot.add_cog(Events(bot))
