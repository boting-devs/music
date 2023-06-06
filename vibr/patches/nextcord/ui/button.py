from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nextcord import ButtonStyle, ui

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

    from nextcord import Emoji, PartialEmoji
    from nextcord.ui import Button, View

    from vibr.inter import Inter

    ViewT = TypeVar("ViewT", bound="View")

    CallbackType = Callable[
        [Any, Button[ViewT], Inter],
        Coroutine[Any, Any, None],
    ]

__all__ = ("button",)


def button(
    *,
    label: str | None = None,
    custom_id: str | None = None,
    disabled: bool = False,
    style: ButtonStyle = ButtonStyle.secondary,
    emoji: str | Emoji | PartialEmoji | None = None,
    row: int | None = None,
) -> Callable[[CallbackType], CallbackType]:
    return ui.button(
        label=label,
        custom_id=custom_id,
        disabled=disabled,
        style=style,
        emoji=emoji,
        row=row,
    )  # pyright: ignore[reportGeneralTypeIssues]
