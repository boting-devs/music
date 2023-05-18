from __future__ import annotations

from typing import TYPE_CHECKING

from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

if TYPE_CHECKING:
    from nextcord import StageChannel, VoiceChannel


__all__ = ("AlreadyConnected",)


class AlreadyConnected(CheckFailure):
    def __init__(self, channel: VoiceChannel | StageChannel) -> None:
        self.embed = ErrorEmbed(
            title="I Am Already Connected",
            description=f"I am already connected to {channel.mention}.",
        )
