from __future__ import annotations

from typing import TYPE_CHECKING

import nextcord
from botbase import MyInter

from vibr.bot import Vibr

if TYPE_CHECKING:
    from vibr.player import Player

__all__ = ("Inter",)


class Inter(MyInter[Vibr]):
    @property
    def guild(self) -> Guild:
        return super().guild  # pyright: ignore[reportGeneralTypeIssues]


class Guild(nextcord.Guild):
    @property
    def voice_client(self) -> Player:
        return super().voice_client  # pyright: ignore[reportGeneralTypeIssues]