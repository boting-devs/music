from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("NoTrackOrQuery", "NoPlaylists")


class NoTrackOrQuery(CheckFailure):
    embed = ErrorEmbed(
        title="Nothing Playing and No Query",
        description="Nothing is playing, Enter a query to search for a song to add.",
    )


class NoPlaylists(CheckFailure):
    embed = ErrorEmbed(
        title="Cannot Like a Playlist",
        description="You cannot add a playlist to your liked songs.",
    )
