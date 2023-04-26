from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("NoFilterActive",)


class NoFilterActive(CheckFailure):
    embed = ErrorEmbed(
        title="No Filter Active",
        description="Currently no flter is active.Filter can't be cleared up",
    )
