from __future__ import annotations

from logging import getLogger

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import maintainance
from vibr.db import Notification, User
from vibr.inter import Inter

from ._views import NotificationsMenu, NotificationsSource

log = getLogger(__name__)


class Notifications(CogBase[Vibr]):
    @slash_command()
    async def notifications(self, inter: Inter) -> None:
        ...

    @notifications.subcommand(name="list")
    @maintainance
    async def notifications_list(self, inter: Inter) -> None:
        """List all notifications."""

        count = await Notification.count()

        if not count:
            await inter.send("No notifications available.")
            return

        source = NotificationsSource(total=count)
        menu = NotificationsMenu(source=source)
        await menu.start(interaction=inter, ephemeral=True)

    @notifications.subcommand(name="enable")
    @maintainance
    async def notifications_enable(self, inter: Inter) -> None:
        """Enable notifications for news."""

        await User.insert(
            User({User.id: inter.user.id, User.notifications: True})
        ).on_conflict((User.id,), "DO UPDATE", (User.notifications,))
        log.info("Enabled notifications for %d", inter.user.id)

        await inter.send("Notifications have been enabled.", ephemeral=True)

    # Now notifications disable
    @notifications.subcommand(name="disable")
    @maintainance
    async def notifications_disable(self, inter: Inter) -> None:
        """Disable notifications for news."""

        await User.insert(
            User({User.id: inter.user.id, User.notifications: False})
        ).on_conflict((User.id,), "DO UPDATE", (User.notifications,))

        await inter.send("Notifications have been disabled.", ephemeral=True)


def setup(bot: Vibr) -> None:
    bot.add_cog(Notifications(bot))
