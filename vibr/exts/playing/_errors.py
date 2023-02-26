from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("NoTracksFound",)


class NoTracksFound(CheckFailure):
    embed = ErrorEmbed(
        title="No Tracks Found",
        description="Could not find any tracks for your config. "
        "Try a different `search-type` or a more generic query.",
    )
