from __future__ import annotations
from base64 import b64encode

from logging import getLogger

import mafic
from botbase import CogBase
from mafic import SearchType
from nextcord import SlashOption, slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected
from vibr.database import add_to_liked, remove_from_liked
from vibr.db import Playlist, PlaylistToSong
from vibr.db.playlists import Song
from vibr.embed import Embed
from vibr.errors import NoTracksFound
from vibr.inter import Inter
from vibr.views import SearchView

from ._errors import *
from ._views import LikedMenu, LikedSource

log = getLogger(__name__)


class Liked(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    async def liked(self, inter: Inter) -> None:
        ...

    SEARCH_TYPE = SlashOption(
        name="search-type",
        choices={
            "Default": SearchType.YOUTUBE.value,
            "SoundCloud": SearchType.SOUNDCLOUD.value,
            "Spotify": SearchType.SPOTIFY_SEARCH.value,
            "Apple Music": SearchType.APPLE_MUSIC.value,
            "Deezer": SearchType.DEEZER_SEARCH.value,
        },
        default=SearchType.YOUTUBE.value,
    )

    @liked.subcommand(name="add")
    async def liked_add(
        self,
        inter: Inter,
        query: str | None = None,
        search_type: str | None = SEARCH_TYPE,
    ) -> None:
        """Add a song to your liked songs playlist.

        query:
            Can be a URL/link, query or past played song.
            Leave blank to use the currently playing song.
        search_type:
            The platform to search if this is a query.
        """

        await inter.response.defer(ephemeral=True)

        track = inter.guild.voice_client and inter.guild.voice_client.current

        if query:
            node = self.bot.pool.label_to_node["LOCAL"]
            result = await node.fetch_tracks(
                query, search_type=search_type or "youtube"
            )

            if not result:
                raise NoTracksFound

            if isinstance(result, mafic.Playlist):
                raise NoPlaylists

            view = SearchView(result)
            embed = view.create_search_embed(tracks=result)
            await inter.edit_original_message(embed=embed, view=view)
            view.message = inter

            await view.wait()

            track_index = view.selected_track
            track = result[track_index] if track_index is not None else None

            if track is None:
                return

        elif track is None:
            raise NoTrackOrQuery

        log.info("Adding %s to %d's liked songs playlist", track.title, inter.author.id)
        existed = await add_to_liked(user=inter.author, track=track)

        if existed:
            await inter.edit_original_message(
                content=f"**{track.title}** is already in your liked songs playlist.",
                embed=None,
                view=None,
            )
            return

        await inter.edit_original_message(
            content=f"Added **{track.title}** to your liked songs playlist.",
            embed=None,
            view=None,
        )

    @liked.subcommand(name="remove")
    async def liked_remove(self, inter: Inter, index: int) -> None:
        """Remove a song from your liked songs playlist.

        index:
            The index of the song to remove.
            This can be found by using the `/liked list` command.
        """

        await inter.response.defer(ephemeral=True)

        index -= 1
        lavalink_id = await remove_from_liked(user=inter.author, index=index)
        log.info("Removed %d from %d's liked songs playlist", index, inter.author.id)

        if lavalink_id is None:
            raise NoSongAtIndex(self.bot)

        node = self.bot.pool.label_to_node["LOCAL"]
        track = await node.decode_track(lavalink_id)
        await inter.send(
            f"Removed **{track.title}** from your liked songs playlist.",
            ephemeral=True,
        )

    @liked.subcommand(name="list")
    async def liked_list(self, inter: Inter) -> None:
        """List your liked songs playlist."""

        playlist = await Playlist.objects().get(
            (Playlist.owner.id == inter.user.id) & (Playlist.name == "Liked Songs")
        )
        if playlist is None:
            raise NoLikedSongs(self.bot)

        count = await PlaylistToSong.count().where(
            PlaylistToSong.playlist == playlist.id
        )
        if count == 0:
            raise NoLikedSongs(self.bot)

        source = LikedSource(bot=self.bot, count=count, playlist=playlist)
        menu = LikedMenu(source=source)
        await menu.start(interaction=inter)

    @liked.subcommand(name="play")
    @is_connected
    async def liked_play(self, inter: Inter) -> None:
        """Play your liked songs playlist."""

        player = inter.guild.voice_client

        playlist = await Playlist.objects().get(
            (Playlist.owner.id == inter.user.id) & (Playlist.name == "Liked Songs")
        )
        if playlist is None:
            raise NoLikedSongs(self.bot)

        songs: list[Song] = await playlist.get_m2m(playlist.songs)
        if not songs:
            raise NoLikedSongs(self.bot)

        tracks = await inter.guild.voice_client.node.decode_tracks(
            [b64encode(song.lavalink_id).decode() for song in songs]
        )
        if player.current is None:
            await player.play(tracks[0])
            tracks = tracks[1:]

        player.queue.extend(tracks)

        embed = Embed(title="Liked Songs", description=f"Added {len(tracks)} songs.")
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Liked(bot))
