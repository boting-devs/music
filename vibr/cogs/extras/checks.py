from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ext.application_checks import check

from .errors import NotConnected

if TYPE_CHECKING:
    from .types import MyInter


__all__ = ("connected",)


def connected():
    async def extended_check(inter: MyInter) -> bool:
        if inter.guild.voice_client is None:
            raise NotConnected()

        return True

    return check(extended_check)  # type: ignore
