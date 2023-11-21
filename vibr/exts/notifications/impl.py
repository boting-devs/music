from __future__ import annotations

from logging import getLogger
from typing import Any

from asyncache import cached
from botbase import CogBase
from cachetools import TTLCache
from cachetools.keys import hashkey
from nextcord import Permissions, slash_command
from nextcord.ext.application_checks import is_owner
from nextcord.utils import utcnow
from prometheus_client import Counter

from vibr.bot import Vibr
from vibr.db import Notification, User
from vibr.inter import Inter

from ._modals import CreateNotification

log = getLogger(__name__)

CACHE = TTLCache[tuple[Any], bool](maxsize=2e20, ttl=60 * 60)
FORMAT = (
    "{mention} You have a new notification with the title **{title}** "
    "from `{time}`, see it with {command}"
)


class NotificationsImpl(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)
        self.notified = Counter("vibr_notified_users", "User notifications sent")

    # Remove `self` (`key`).
    @cached(CACHE, key=lambda *args, **kwargs: hashkey(*args[1:], **kwargs))
    async def get_notified_status(self, user: int) -> bool:
        data = (
            await User.select(User.notified, User.notifications)
            .where(User.id == user)
            .first()
        )

        # They have actually been notified, or don't want notifications.
        return ((data["notified"]) or not data["notifications"]) if data else False

    @CogBase.listener()
    async def on_application_command_completion(self, inter: Inter) -> None:
        return
        notified = await self.get_notified_status(inter.user.id)

        if not notified:
            notification = await (
                Notification.select()
                .where(Notification.expires > utcnow())
                .order_by(Notification.id, ascending=False)
                .limit(1)
                .first()
            )

            if notification:
                await inter.send(
                    FORMAT.format(
                        mention=inter.user.mention,
                        title=notification["title"],
                        time=notification["posted"].strftime("%d %b %Y"),
                        command=self.bot.get_command_mention("notifications list"),
                    ),
                    ephemeral=True,
                )
                log.info("Notified %d", inter.user.id)
                self.notified.inc()

            await User.insert(
                User({User.id: inter.user.id, User.notified: True})
            ).on_conflict((User.id,), "DO UPDATE", ((User.notified, True),))
            CACHE[hashkey(inter.user.id)] = True

    @slash_command(
        name="create-notification", default_member_permissions=Permissions(8)
    )
    @is_owner()
    async def create_notification(self, inter: Inter) -> None:
        """Create a notification."""

        await inter.response.send_modal(CreateNotification())


def setup(bot: Vibr) -> None:
    bot.add_cog(NotificationsImpl(bot))
