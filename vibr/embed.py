from __future__ import annotations

from functools import cached_property
from random import choice
from typing import TYPE_CHECKING, Any

from nextcord import ButtonStyle
from nextcord import Embed as NextcordEmbed
from nextcord.ui import Button, View

from vibr.constants import COLOURS, SUPPORT_URL

if TYPE_CHECKING:
    from datetime import datetime

    from nextcord import Colour, embeds

    EmbedType = embeds.EmbedType  # pyright: ignore[reportPrivateImportUsage]


__all__ = ("Embed",)


class Embed(NextcordEmbed):
    def __init__(
        self,
        *,
        colour: int | Colour | None = None,
        color: int | Colour | None = None,
        title: Any | None = None,
        type: EmbedType = "rich",
        url: Any | None = None,
        description: Any | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        super().__init__(
            colour=colour or color or choice(COLOURS),
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )


class SupportView(View):
    def __init__(self) -> None:
        super().__init__(timeout=0)

        self.add_item(
            Button(label="Support Server", style=ButtonStyle.link, url=SUPPORT_URL)
        )


class ErrorEmbed(Embed):
    def __init__(
        self,
        *,
        colour: int | Colour | None = None,
        color: int | Colour | None = None,
        title: Any | None = None,
        type: EmbedType = "rich",
        url: Any | None = None,
        description: Any | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        super().__init__(
            colour=colour,
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.set_footer(
            text="If you believe this to be in error, please join the support server."
        )

    @cached_property
    def view(self) -> SupportView:
        return SupportView()
