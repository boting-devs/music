from nextcord.ext.commands import CheckFailure


class NotInVoice(CheckFailure):
    """Raised when author is not in a voice channel."""


class NotConnected(CheckFailure):
    """Raised when bot isnt connected to a channel."""
