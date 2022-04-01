from __future__ import annotations

from typing import TYPE_CHECKING

from botbase.checks import check

from .errors import NotConnected

if TYPE_CHECKING:
    from .types import MyContext, MyInter


__all__ = ("connected",)


def connected():
    async def extended_check(ctx: MyContext | MyInter) -> bool:
        if ctx.voice_client is None:
            raise NotConnected()

        return True

    return check(extended_check)
