from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = (
    "AlreadyPaused",
    "AlreadyResumed"
)

class AlreadyPaused(CheckFailure):
    embed=ErrorEmbed(
        title="Already paused",
        description="Song is already paused.\nUse /resume to resume your song."
    )

class AlreadyResumed(CheckFailure):
    embed = ErrorEmbed(
        title="Song is playing",
        description="Song is already playing in your voice-channel"
    )
