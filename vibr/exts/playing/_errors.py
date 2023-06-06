from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = (
    "AmountNotInt",
    "IndexNotInQueue",
    "QueueEmpty",
    "SongNotProvided",
    "LyricsNotFound",
)


class AmountNotInt(CheckFailure):
    embed = ErrorEmbed(
        title="Amount Must Be a Number",
        description="`amount` must be a number, indicating how many tracks you want to "
        "skip. To help you with this, use the autocomplete that pops up when typing in "
        "the track name.",
    )


class IndexNotInQueue(CheckFailure):
    embed = ErrorEmbed(
        title="Index Not in Queue",
        description="The amount you provided goes over the end of the queue. "
        "To help you get the right amount, start typing into `to` and use the "
        "autocomplete that pops up.",
    )


class QueueEmpty(CheckFailure):
    embed = ErrorEmbed(
        title="Queue Empty",
        description="The queue is empty. There is nothing to skip.",
    )


class SongNotProvided(CheckFailure):
    embed = ErrorEmbed(
        title="No Song Provided", description="Please provide a song for lyrics!"
    )


class LyricsNotFound(CheckFailure):
    embed = ErrorEmbed(
        title="No Lyrics Found",
        description="Sorry, could not find lyrics for that track :(",
    )
