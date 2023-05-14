from __future__ import annotations

from asyncio import gather
from datetime import UTC, datetime
from os import environ
from typing import TYPE_CHECKING, cast

from botbase import CogBase
from itsdangerous import URLSafeSerializer
from mafic import Playlist, Track
from nextcord import ApplicationCommandType, slash_command
from nextcord.utils import get
from ormar import NoMatch

from vibr.bot import Vibr
from vibr.db import User
from vibr.embed import Embed
from vibr.inter import Inter
from vibr.track_embed import track_embed

from ._types import SpotifyPlaylist, TracksResponse
from ._views import PlaylistMenu, PlaylistSource

if TYPE_CHECKING:
    from async_spotify.authentification import SpotifyAuthorisationToken

    from ._types import PlaylistResponse, SpotifyTrackInfo


PLAYLIST_PAGE_LIMIT = 100
PLAYLIST_ITEMS_FIELDS = (
    "total,items(is_local, track(external_urls.spotify,id,name,"
    "duration_ms,artists.name,external_ids.isrc,album.images.url))"
)
PLAYLIST_FIELDS = "id,name,images.url"


class Spotify(CogBase[Vibr]):
    AUTHORIZE_URL = f"{environ['SPOTIFY_REDIRECT_URL']}/spotify/authorize"

    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)

        self.serializer = URLSafeSerializer(
            secret_key=environ["OAUTH_SECRET_KEY"], salt="vibr"
        )

    @slash_command(dm_permission=False)
    async def spotify(self, inter: Inter) -> None:
        ...

    @spotify.subcommand(name="link")
    async def spotify_link(self, inter: Inter) -> None:
        """Link your spotify account."""

        signed_user_id = self.serializer.dumps(inter.user.id)
        await inter.send(f"{self.AUTHORIZE_URL}/?user={signed_user_id}")

    @spotify.subcommand(name="unlink")
    async def spotify_unlink(self, inter: Inter) -> None:
        """Unlink your spotify account."""

        try:
            user = await User.objects.get(id=inter.user.id)
        except NoMatch:
            embed = Embed(
                title="Not Linked", description="You are not linked to spotify."
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        if user.spotify_access_token is None:
            embed = Embed(
                title="Not Linked", description="You are not linked to spotify."
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        user.spotify_access_token = None
        user.spotify_refresh_token = None
        user.spotify_token_expires = None
        await user.update()

        embed = Embed(title="Unlinked", description="Your account has been unlinked.")
        await inter.send(embed=embed, ephemeral=True)

    @spotify.subcommand(name="playlists")
    async def spotify_playlists(self, inter: Inter) -> None:
        """List your spotify playlists."""

        try:
            user = await User.objects.get(id=inter.user.id)
        except NoMatch:
            embed = Embed(
                title="Not Linked", description="You are not linked to spotify."
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        token = user.spotify
        if token is None:
            embed = Embed(
                title="Not Linked", description="You are not linked to spotify."
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        if token.is_expired():
            token = await self.bot.spotify.refresh_token(token)
            user.spotify_access_token = token.access_token
            user.spotify_refresh_token = token.refresh_token
            user.spotify_activation_time = datetime.fromtimestamp(
                token.activation_time, tz=UTC
            )

        initial = cast(
            "PlaylistResponse",
            await self.bot.spotify.playlists.current_get_all(token, limit=25),
        )
        source = PlaylistSource(initial=initial, token=token, bot=self.bot)
        menu = PlaylistMenu(source=source)
        await menu.start(interaction=inter, ephemeral=True)

        timed_out = await menu.wait()
        if timed_out:
            menu.stop()

        playlist_id = menu.playlist_id

        playlist = cast(
            "SpotifyPlaylist",
            await self.bot.spotify.playlists.get_one(
                playlist_id, token=token, fields=PLAYLIST_FIELDS
            ),
        )

        tracks = await self.get_playlist_tracks(playlist_id, token)

        playlist = self.get_playlist_object(tracks, playlist)
        tracks = playlist.tracks

        if inter.guild.voice_client is None:
            commands = self.bot.get_all_application_commands()
            join = get(commands, name="join", type=ApplicationCommandType.chat_input)
            if not join:
                raise RuntimeError

            await join(inter)

        player = inter.guild.voice_client
        track = tracks[0]

        if player.current is None:
            queued = tracks[1:]
            assert track.uri is not None
            await player.play(track.uri)

            embed = await track_embed(playlist, bot=self.bot, user=inter.user.id)
            await inter.channel.send(embed=embed)  # pyright: ignore

            if queued:
                player.queue += [(track, inter.user.id) for track in queued]
        else:
            player.queue += [(track, inter.user.id) for track in tracks]
            embed = await track_embed(
                playlist, bot=self.bot, user=inter.user.id, queued=True
            )
            await inter.channel.send(embed=embed)  # pyright: ignore

    @staticmethod
    def get_authors(authors: list[str]) -> str:
        if len(authors) == 1:
            return authors[0]

        return f"{', '.join(authors[:-1])} and {authors[-1]}"

    def get_playlist_object(
        self, tracks: list[SpotifyTrackInfo], playlist: SpotifyPlaylist
    ) -> Playlist:
        track_objects = [
            Track(
                track_id="",
                identifier=track["id"],
                title=track["name"],
                author=self.get_authors(
                    [artist["name"] for artist in track["artists"]]
                ),
                length=track["duration_ms"],
                isrc=track["external_ids"]["isrc"],
                artwork_url=track["album"]["images"][0]["url"],
                source="spotify",
                seekable=True,
                stream=False,
                uri=track["external_urls"]["spotify"],
            )
            for track in tracks
        ]
        playlist_object = Playlist(
            info={
                "name": playlist["name"],
                "selectedTrack": 0,
            },
            tracks=[],
            plugin_info={"artworkUrl": playlist["images"][0]["url"]},
        )
        playlist_object.tracks = track_objects

        return playlist_object

    async def get_playlist_tracks(
        self, playlist_id: str, token: SpotifyAuthorisationToken
    ) -> list[SpotifyTrackInfo]:
        first_tracks = cast(
            TracksResponse,
            await self.bot.spotify.playlists.get_tracks(
                playlist_id, auth_token=token, limit=100, fields=PLAYLIST_ITEMS_FIELDS
            ),
        )
        total = first_tracks["total"]
        tracks = first_tracks["items"]

        if total > PLAYLIST_PAGE_LIMIT:
            responses: list[TracksResponse] = await gather(
                *(
                    self.bot.spotify.playlists.get_tracks(
                        playlist_id,
                        auth_token=token,
                        limit=100,
                        offset=offset,
                        fields=PLAYLIST_ITEMS_FIELDS,
                    )
                    for offset in range(100, total, 100)
                )
            )
            for data in responses:
                tracks.extend(
                    [track for track in data["items"] if not track["is_local"]]
                )

        return [track["track"] for track in tracks]


def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))
