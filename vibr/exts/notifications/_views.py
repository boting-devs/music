from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord import ButtonStyle
from nextcord.ext.menus import ButtonMenuPages, PageSource
from nextcord.utils import utcnow

from vibr.db import Notification
from vibr.embed import Embed

if TYPE_CHECKING:
    from typing import Any

FORMAT = "**{title}**\n{description}"


class NotificationsSource(PageSource):
    def __init__(self, *, total: int) -> None:
        self.total = total

    def is_paginating(self) -> bool:
        return self.total > 1

    def get_max_pages(self) -> int | None:
        return self.total

    async def get_page(self, page_number: int) -> dict[str, Any]:
        notification = (
            await Notification.select(
                Notification.title,
                Notification.description,
                Notification.posted,
            )
            .where(Notification.expires > utcnow())
            .offset(page_number)
            .limit(1)
            .first()
        )
        assert notification is not None
        return notification

    async def format_page(
        self, _menu: NotificationsMenu, notification: dict[str, Any]
    ) -> Embed:
        embed = Embed(
            description=FORMAT.format(
                title=notification["title"], description=notification["description"]
            )
        )

        embed.set_author(name=f"Notifications (total: {self.total})")
        embed.set_footer(text=notification["posted"].strftime("%d %b %Y"))

        return embed


class NotificationsMenu(ButtonMenuPages):
    def __init__(self, source: NotificationsSource) -> None:
        super().__init__(source, style=ButtonStyle.blurple)
