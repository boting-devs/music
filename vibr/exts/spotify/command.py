from __future__ import annotations

import re
from os import environ
from typing import TYPE_CHECKING, cast

from botbase import CogBase
from discord import SlashOption
from itsdangerous import URLSafeSerializer
from nextcord import slash_command
from ormar import NoMatch

from vibr.bot import Vibr
from vibr.db import User
from vibr.embed import Embed
from vibr.inter import Inter

from ._errors import InvalidSpotifyUrl, NotLinked
from ._views import PlaylistMenu, PlaylistSource

if TYPE_CHECKING:
    from ._types import PlaylistResponse


PLAYLIST_PAGE_LIMIT = 100
PLAYLIST_ITEMS_FIELDS = (
    "total,items(is_local, track(external_urls.spotify,id,name,"
    "duration_ms,artists.name,external_ids.isrc,album.images.url))"
)
PLAYLIST_FIELDS = "id,name,images.url"


class Spotify(CogBase[Vibr]):
    PLAYLIST_URL = "https://open.spotify.com/playlist/"
    SPOTIFY_URL_REGEX = re.compile(
        r"^https?:\/\/open.spotify.com\/user\/(?P<id>(?:(?!\?).)*).*$"
    )
    """A pattern to match user profile URLs.

    e.g. https://open.spotify.com/user/uwv4xcjfd79as24pcpckc9grb?si=c1c4d421a1f54b93
    """

    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)

        self.serializer = URLSafeSerializer(
            secret_key=environ["OAUTH_SECRET_KEY"], salt="vibr"
        )

    @slash_command(dm_permission=False)
    async def spotify(self, inter: Inter) -> None:
        ...

    PROFILE_URL = SlashOption(name="profile-url")

    @spotify.subcommand(name="link")
    async def spotify_link(self, inter: Inter, profile_url: str = PROFILE_URL) -> None:
        """Link your spotify account.

        profile_url:
            The link to your Spotify profile.
        """

        if not (match := self.SPOTIFY_URL_REGEX.match(profile_url)):
            raise InvalidSpotifyUrl

        spotify_id = match.group("id")

        try:
            user = await User.objects.get(id=inter.user.id)
        except NoMatch:
            await User.objects.create(id=inter.user.id, spotify_id=spotify_id)
        else:
            user.spotify_id = spotify_id
            await user.update()

        embed = Embed(
            title="Linked to Spotify", description="Successfully linked to Spotify!"
        )
        await inter.send(embed=embed, ephemeral=True)

    @spotify.subcommand(name="unlink")
    async def spotify_unlink(self, inter: Inter) -> None:
        """Unlink your spotify account."""

        try:
            user = await User.objects.get(id=inter.user.id)
        except NoMatch as e:
            raise NotLinked(self.bot) from e

        if user.spotify_id is None:
            raise NotLinked(self.bot)

        user.spotify_id = None
        await user.update()

        embed = Embed(title="Unlinked", description="Your account has been unlinked.")
        await inter.send(embed=embed, ephemeral=True)

    @spotify.subcommand(name="playlists")
    async def spotify_playlists(self, inter: Inter) -> None:
        """List your spotify playlists."""

        try:
            user = await User.objects.get(id=inter.user.id)
        except NoMatch as e:
            raise NotLinked(self.bot) from e

        user_id = user.spotify_id
        if user_id is None:
            raise NotLinked(self.bot)

        initial = cast(
            "PlaylistResponse",
            await self.bot.spotify.playlists.get_user_all(user_id, limit=25),
        )
        source = PlaylistSource(initial=initial, user_id=user_id, bot=self.bot)
        menu = PlaylistMenu(source=source)
        await menu.start(interaction=inter, ephemeral=True)

        timed_out = await menu.wait()
        if timed_out:
            menu.stop()

        playlist = menu.playlist_id

        await self.bot.play(inter=inter, query=self.PLAYLIST_URL + playlist)


def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))
