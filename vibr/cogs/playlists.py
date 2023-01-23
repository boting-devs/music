from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Optional

from nextcord import slash_command
from nextcord.ext.commands import Cog
from pomice import Playlist

from .error import NotConnected
from .extras.playing_embed import playing_embed
from .extras.types import MyInter
from .extras.views import (
    SearchView,
    UserPlaylistSource,
    UserPlaylistView,
    create_search_embed,
)
from .music import Music

if TYPE_CHECKING:
    from pomice import Track

    from ..__main__ import Vibr

log = getLogger(__name__)

class Playlists(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot

    @slash_command()
    async def liked(self, _: MyInter):
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

            ORDER BY song_to_playlist.added ASC;
            """,
            inter.user.id,
        )

        if not songs:
            return await inter.send_author_embed(
                "You have no liked songs, use /liked add to add to your liked songs."
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

        track = (
            inter.guild
            and inter.guild.voice_client
            and inter.guild.voice_client.current
        )
        if query is not None:
            if inter.guild is None or inter.guild.voice_client is None:
                raise NotConnected

            tracks = await inter.guild.voice_client.get_tracks(
                query=query,
                ctx=inter,  # type: ignore
            )

            if not tracks:
                return await inter.send_author_embed("No tracks found")
            elif isinstance(tracks, Playlist):
                return await inter.send_author_embed(
                    "You cannot add a playlist to your liked songs right now."
                )

            view = SearchView(tracks)

            m = await inter.send(
                embed=create_search_embed(bot=self.bot, tracks=tracks), view=view
            )
            view.message = m  # type: ignore
            await view.wait()
            if view.selected_track is None:
                return await inter.send_author_embed("No track selected.")

            track = view.selected_track

        elif track is None:
            return await inter.send_embed(
                "No Track Given",
                "Something must be playing or `query` must be specified.",
            )

        songs = await self.bot.db.fetch(
            """SELECT
                song_data.lavalink_id, song_data.uri, song_data.spotify
            FROM song_data

            INNER JOIN song_to_playlist
            ON song_to_playlist.song = song_data.id

            INNER JOIN playlists
            ON playlists.id = song_to_playlist.playlist

            WHERE playlists.id = (
                SELECT id FROM playlists WHERE owner=$1 AND name='Liked Songs'
            )

            ORDER BY song_to_playlist.added ASC;
            """,
            inter.user.id,
        )

        for song in songs:
            if song["uri"] == track.uri:
                return await inter.send("Song already in liked list")

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

    @liked.subcommand(name="remove")
    async def like_remove(self, inter: MyInter, index: int):
        """Remove a song from your liked list.

        index:
            The number of the song to remove, found in /liked list.
        """
        index = index - 1

        songs = await self.bot.db.fetch(
            """SELECT song_data.id, song_data.name FROM song_data

            INNER JOIN song_to_playlist
            ON song_to_playlist.song = song_data.id

            INNER JOIN playlists
            ON playlists.id = song_to_playlist.playlist

            WHERE playlists.id = (
                SELECT id FROM playlists WHERE owner=$1 AND name='Liked Songs'
            )

            ORDER BY song_to_playlist.added ASC;
            """,
            inter.user.id,
        )

        if index >= len(songs):
            return await inter.send_author_embed("Invalid index.")

        song = songs[index]

        async with inter.bot.db.acquire() as con:
            async with con.transaction():
                await con.execute(
                    """DELETE FROM song_to_playlist
                    WHERE song = $1 AND playlist = (
                        SELECT id FROM playlists WHERE owner = $2
                    )""",
                    song["id"],
                    inter.user.id,
                )
                await con.execute(
                    """UPDATE song_data SET likes = song_data.likes - 1
                    WHERE id = $1""",
                    song["id"],
                )

        await inter.send(f"Removed `{song['name']}` from your liked songs!")

    @liked.subcommand(name="play")
    async def liked_play(self, inter: MyInter):
        """Play your liked songs."""

        if inter.guild is None:
            raise NotConnected

        if not inter.guild.voice_client:
            await Music.join(inter)

        player = inter.guild.voice_client

        songs = await self.bot.db.fetch(
            """SELECT
                song_data.lavalink_id, song_data.uri, song_data.spotify
            FROM song_data

            INNER JOIN song_to_playlist
            ON song_to_playlist.song = song_data.id

            INNER JOIN playlists
            ON playlists.id = song_to_playlist.playlist

            WHERE playlists.id = (
                SELECT id FROM playlists WHERE owner=$1 AND name='Liked Songs'
            )

            ORDER BY song_to_playlist.added ASC;
            """,
            inter.user.id,
        )

        if not songs:
            return await inter.send_author_embed(
                "You have no liked songs, use /liked add to add to your liked songs."
            )

        tracks: list[Track] = []

        for song in songs:
            if song["spotify"]:
                result = await player.get_tracks(
                    song["uri"],
                    ctx=inter,  # type: ignore
                )
                assert not isinstance(result, Playlist)

                if not result:
                    continue

                track = result[0]
            else:
                track = await player.node.build_track(song["lavalink_id"], ctx=inter)  # type: ignore

            tracks.append(track)

        if not tracks:
            return await inter.send_author_embed("No tracks found.")

        if not player.queue and not player.is_playing:
            track = tracks[0]
            toplay = tracks[1:]

            if len(player.queue) + len(toplay) > 500:
                amount = 500 - len(player.queue)
                await inter.send_author_embed(f"Queueing {amount} tracks...")
                toplay = toplay[:amount]

            await player.play(track=track)
            
            await playing_embed(tracks[0],liked=True)
        else:
            toplay = tracks
            if len(player.queue) + len(toplay) > 500:
                amount = 500 - len(player.queue)
                await inter.send_author_embed(f"Queueing {amount} tracks...")
                toplay = toplay[:amount]

            await playing_embed(tracks[0], queue=True)

        if toplay:
            player.queue += toplay


def setup(bot: Vibr):
    bot.add_cog(Playlists(bot))
