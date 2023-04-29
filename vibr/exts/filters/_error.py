from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("NoFilterActive",
           "InvalidSpeed",)


class NoFilterActive(CheckFailure):
    embed = ErrorEmbed(
        title="No Filter Active",
        description="Currently no flter is active.Filter can't be cleared up",
    )

class InvalidSpeed(CheckFailure):
    embed=ErrorEmbed(
        title="Invalid Speed",
        description="Please use the speed betweeen 0 and 2"
    )
