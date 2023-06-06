from __future__ import annotations

from datetime import timedelta
from logging import getLogger

from humanfriendly import parse_timespan
from nextcord import TextInputStyle
from nextcord.ui import Modal, TextInput
from nextcord.utils import utcnow

from vibr.db import Notification, User
from vibr.inter import Inter

log = getLogger(__name__)


class CreateNotification(Modal):
    def __init__(self) -> None:
        super().__init__(title="Create a Notification")

        self._title = TextInput(
            label="Notification title", max_length=256, required=True
        )
        self.description = TextInput(
            label="Notification description",
            style=TextInputStyle.paragraph,
            required=True,
        )
        self.expiry = TextInput(
            label="Expiry interval", default_value="7d", required=True
        )

        self.add_item(self._title)
        self.add_item(self.description)
        self.add_item(self.expiry)

    async def callback(self, inter: Inter) -> None:
        title = self._title.value
        description = self.description.value
        expiry = self.expiry.value
        assert title is not None
        assert description is not None
        assert expiry is not None

        try:
            interval = timedelta(seconds=parse_timespan(expiry))
        except ValueError:
            await inter.send("Invalid interval, please try again.", ephemeral=True)
            return

        now = utcnow()
        await Notification.insert(
            Notification(
                {
                    Notification.title: title,
                    Notification.description: description,
                    Notification.posted: now,
                    Notification.expires: now + interval,
                }
            )
        )
        await User.update({User.notified: False}, force=True)

        from .impl import CACHE

        CACHE.clear()

        await inter.send("Notification created!")
        log.info("Notification created")
