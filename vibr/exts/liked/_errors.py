from vibr.bot import Vibr
from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("NoTrackOrQuery", "NoPlaylists", "NoSongAtIndex", "NoLikedSongs")


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


class NoSongAtIndex(CheckFailure):
    def __init__(self, bot: Vibr) -> None:
        self.embed = ErrorEmbed(
            title="No Track Found",
            description=(
                "Could not find a track at that index. "
                "Try again by checking the index at "
                f"{bot.get_command_mention('liked list')}"
            ),
        )


class NoLikedSongs(CheckFailure):
    def __init__(self, bot: Vibr) -> None:
        self.embed = ErrorEmbed(
            title="No Liked Songs",
            description=(
                "You do not have any liked songs. Add some using "
                f"{bot.get_command_mention('liked add')}"
            ),
        )
