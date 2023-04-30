from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("NoFilterActive",
           "InvalidSpeed",
           "SpeedNotActive",)


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

class SpeedNotActive(CheckFailure):
    embed = ErrorEmbed(
        title="Speed Not Active",
        description="Please input the speed as specified in the query box"
    )
