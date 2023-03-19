from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = (
    "NoTracksFound",
    "AmountAndToProvided",
    "ToNotIndex",
    "IndexNotInQueue",
    "QueueEmpty",
)


class NoTracksFound(CheckFailure):
    embed = ErrorEmbed(
        title="No Tracks Found",
        description="Could not find any tracks for your config. "
        "Try a different `search-type` or a more generic query.",
    )


class AmountAndToProvided(CheckFailure):
    embed = ErrorEmbed(
        title="Amount and To Cannot Both Be Provided",
        description="`amount` and `to` cannot both be provided. "
        "Please use one or the other. `amount` is for numerical skipping, "
        "`to` is to skip up until a certain track",
    )


class ToNotIndex(CheckFailure):
    embed = ErrorEmbed(
        title="To Must Be a Number",
        description="`to` must be a number, indicating where in the queue the track "
        "you want to skip to is. To help you with this, use the autocomplete that pops "
        "up when typing in the track name.",
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
