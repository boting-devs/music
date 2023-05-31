from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from nextcord import ApplicationCheckFailure, StageChannel, VoiceChannel
from nextcord.ui import Button, View

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
    "VoiceConnectionError",
    "QueueFull",
    "NotVoted",
    "MaxLiked",
)


class CheckFailure(ApplicationCheckFailure, ABC):
    embed: ErrorEmbed
    view: View | None = None


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


class VoiceConnectionError(CheckFailure):
    embed = ErrorEmbed(
        title="Failed to Connect",
        description=(
            "Failed to connect to the vocie channel. Please try again later.",
        ),
    )


class QueueFull(CheckFailure):
    embed = ErrorEmbed(
        title="Queue Full",
        description="The queue is full, you cannot add more tracks.",
    )


class NotVoted(CheckFailure):
    def __init__(self, bot: Vibr) -> None:
        self.view = View()
        self.view.add_item(
            Button(label="Vote", url="https://top.gg/bot/882491278581977179/vote")
        )
        self.embed = ErrorEmbed(
            title="Not Voted",
            description=(
                "This command requires a vote. Use the link below or "
                f"{bot.get_command_mention('vote')}."
            ),
        )


class MaxLiked(CheckFailure):
    embed = ErrorEmbed(
        title="Max Liked Songs", description="You can only have `500` liked songs."
    )
