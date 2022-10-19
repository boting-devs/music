from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from nextcord import slash_command
from nextcord.ext.commands import Cog

from .extras.types import MyInter
from .extras.views import UserPlaylistSource, UserPlaylistView

if TYPE_CHECKING:
    from ..__main__ import Vibr


class Playlists(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot

    @slash_command()
    async def liked(self):
        ...

    @liked.subcommand(name="list")
    async def liked_list(self, inter: MyInter):
        """List all the songs you have added to your liked playlist."""

        songs = await self.bot.db.fetch(
            """SELECT
                song_data.name,
                song_data.artist,
                song_data.length,
                song_data.uri,
                song_to_playlist.added
            FROM song_data

            INNER JOIN song_to_playlist
            ON song_to_playlist.song = song_data.id

            INNER JOIN playlists
            ON playlists.id = song_to_playlist.playlist

            WHERE playlists.id = (
                SELECT id FROM playlists WHERE owner=$1 AND name='Liked Songs'
            )
            """,
            inter.user.id,
        )

        view = UserPlaylistView(
            source=UserPlaylistSource(title="Liked Songs", songs=songs)
        )
        await view.start(interaction=inter)

    @liked.subcommand(name="add")
    async def like_add(self, inter: MyInter, query: Optional[str] = None):
        """Add a new song to your liked playlist.

        query:
            The song you want to add to your liked playlist,
            do not specify if this should be the current song.
        """

        track = inter.guild.voice_client.current
        if track is None and query is None:
            # TODO: give user an error saying one is required
            raise RuntimeError(...)
        elif track is None:
            # TODO: search for song - maybe giving the user a full 25 song list
            return

        async with inter.bot.db.acquire() as con:
            async with con.transaction():
                await con.execute(
                    """INSERT INTO song_data
                    (id,
                    lavalink_id,
                    spotify,
                    name,
                    artist,
                    length,
                    thumbnail,
                    uri)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT (id)
                    DO UPDATE SET likes = song_data.likes + 1
                    """,
                    track.identifier,
                    track.track_id,
                    track.spotify,
                    track.title,
                    track.author,
                    track.length / 1000 if track.length is not None else 0,
                    track.thumbnail,
                    track.uri,
                )
                await con.execute(
                    """INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING""",
                    inter.user.id,
                )
                await con.execute(
                    """INSERT INTO PLAYLISTS (owner)
                    VALUES ($1) ON CONFLICT DO NOTHING""",
                    inter.user.id,
                )
                await con.execute(
                    """INSERT INTO song_to_playlist (song, playlist)
                    VALUES ($1, (SELECT id FROM playlists WHERE owner = $2))
                    ON CONFLICT DO NOTHING""",
                    track.identifier,
                    inter.user.id,
                )

        await inter.send(f"Saved `{track.title}` to your liked songs!")


def setup(bot: Vibr):
    bot.add_cog(Playlists(bot))
