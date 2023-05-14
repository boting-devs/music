from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("EmptyQueue", "IndexNotInRange", "InvalidIndex")


class EmptyQueue(CheckFailure):
    embed = ErrorEmbed(
        title="Queue is Empty",
        description="The command cannot be used as the queue is empty",
    )


class IndexNotInRange(CheckFailure):
    embed = ErrorEmbed(
        title="Not in Range",
        description="Please use an index within your queue range.",
    )


class InvalidIndex(CheckFailure):
    embed = ErrorEmbed(
        title="Invalid Position",
        description="Please use a number index.",
    )
