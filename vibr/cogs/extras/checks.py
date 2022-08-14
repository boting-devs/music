from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ext.commands import check
from nextcord.ext.application_checks import check as app_check

from .errors import NotConnected

if TYPE_CHECKING:
    from typing import Any, Callable

    from .types import MyContext, MyInter


__all__ = ("connected",)


def connected_p(func: Callable[[Callable], Any]):
    def decorator():
        async def extended_check(ctx: MyContext | MyInter) -> bool:
            if ctx.guild.voice_client is None:
                raise NotConnected()

            return True

        return func(extended_check)

    return decorator


connected = connected_p(check)
connected_a = connected_p(app_check)
