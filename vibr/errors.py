from abc import ABC

from nextcord import ApplicationCheckFailure

from vibr.bot import ErrorEmbed

__all__ = ("CheckFailure",)


class CheckFailure(ApplicationCheckFailure, ABC):
    embed: ErrorEmbed
