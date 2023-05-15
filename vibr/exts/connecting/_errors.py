from __future__ import annotations

from typing import TYPE_CHECKING

from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

if TYPE_CHECKING:
    from nextcord import StageChannel, VoiceChannel


__all__ = ("AlreadyConnected", "UserNotInVoice")


class AlreadyConnected(CheckFailure):
    def __init__(self, channel: VoiceChannel | StageChannel) -> None:
        self.embed = ErrorEmbed(
            title="I Am Already Connected",
            description=f"I am already connected to {channel.mention}.",
        )


class UserNotInVoice(CheckFailure):
    embed = ErrorEmbed(
        title="You Are Not in a Voice Channel",
        description="You are not in a voice channel. Please connect to one or "
        "specify the channel with the `channel` option.",
    )
