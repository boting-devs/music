from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord import slash_command
from nextcord.ext.commands import Cog

from .extras.views import UserPlaylistSource, UserPlaylistView
from .extras.types import MyInter

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

    # @liked.subcommand(name="add")
    # async def like_add(self, inter: MyInter):
    #     player = inter.guild.voice_client.current
    #     if player is not None:
    #         await self.bot.db.execute(
    #             """INSERT INTO song_data
    #                         (id,
    #                         lavalink_id,
    #                         spotify,
    #                         name,
    #                         artist,
    #                         length,
    #                         thumbnail,
    #                         uri)
    #                         VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT (id)
    #                         DO UPDATE SET likes = song_data.likes + 1
    #                         """,
    #             player.identifier,
    #             player.track_id,
    #             player.spotify,
    #             player.title,
    #             player.author,
    #             player.length / 1000 if player.length is not None else 0,
    #             player.thumbnail,
    #             player.uri,
    #         )
    #         await inter.send(f"Saved {player.title} to your liked songs!")
    #     else:
    #         await inter.send("Please play a song to save it")


def setup(bot: Vibr):
    bot.add_cog(Playlists(bot))
