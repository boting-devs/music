from abc import ABC

from nextcord import ApplicationCheckFailure, StageChannel, VoiceChannel

from vibr.bot import ErrorEmbed, Vibr

__all__ = ("CheckFailure", "NotInSameVoice", "NotConnected","NotPlaying")


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
    def __init__(self,bot:Vibr) -> None:
        self.embed = ErrorEmbed(
            title="No song Playing",
            description="Play the song to use the command"
        )