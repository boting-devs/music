from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from nextcord import ApplicationCheckFailure, StageChannel, VoiceChannel

from .embed import ErrorEmbed

if TYPE_CHECKING:
    from vibr.bot import Vibr

__all__ = (
    "CheckFailure",
    "NotInSameVoice",
    "NotConnected",
    "NotPlaying",
    "NoTracksFound",
    "UserNotInVoice",
)


class CheckFailure(ApplicationCheckFailure, ABC):
    embed: ErrorEmbed


class NotInSameVoice(CheckFailure):
    def __init__(self, channel: VoiceChannel | StageChannel) -> None:
        self.embed = ErrorEmbed(
            title="You Are Not in the Same Voice Channel",
            description="You are not in the same voice channel as me! "
            f"I am in {channel.mention}",
        )


class NotConnected(CheckFailure):
    def __init__(self, bot: Vibr) -> None:
        self.embed = ErrorEmbed(
            title="I Am Not Connected",
            description="I am not connected to any voice channel. "
            f"Run {bot.get_command_mention('join')} to connect me!",
        )


class NotPlaying(CheckFailure):
    def __init__(self, bot: Vibr) -> None:
        self.embed = ErrorEmbed(
            title="No song Playing",
            description=f"{bot.get_command_mention('play')} a song to use the command",
        )


class NoTracksFound(CheckFailure):
    embed = ErrorEmbed(
        title="No Tracks Found",
        description="Could not find any tracks for your config. "
        "Try a different `search-type` or a more generic query.",
    )


class UserNotInVoice(CheckFailure):
    embed = ErrorEmbed(
        title="You Are Not in a Voice Channel",
        description="You are not in a voice channel. Please connect to one or "
        "specify the channel with the `channel` option.",
    )
