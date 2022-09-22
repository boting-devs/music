from nextcord.ext.commands import CheckFailure


class NotInVoice(CheckFailure):
    """Raised when author is not in a voice channel."""


class NotConnected(CheckFailure):
    """Raised when bot isnt connected to a channel."""


class TooManyTracks(CheckFailure):
    """Raised when a queue has too many tracks."""


class LyricsNotFound(CheckFailure):
    """Raised when lyrics are not found."""


class NotInSameVoice(CheckFailure):
    """Raised when bot is not in same voice channel."""


class SongNotProvided(CheckFailure):
    """Raised when nothing is playing and lyrics is requested with no arg"""


class Ignore(CheckFailure):
    """An error which should not be handled."""


class VoteRequired(CheckFailure):
    """Raised when a user has not voted for the bot and the command requires it."""
