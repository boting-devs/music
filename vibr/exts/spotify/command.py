from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from async_spotify.spotify_errors import SpotifyAPIError
from botbase import CogBase
from discord import SlashOption
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.db import User
from vibr.embed import Embed
from vibr.inter import Inter

from ._errors import InvalidSpotifyUrl, NotLinked
from ._views import PlaylistMenu, PlaylistSource

if TYPE_CHECKING:
    from ._types import PlaylistResponse


NOT_FOUND = 404


class Spotify(CogBase[Vibr]):
    PLAYLIST_URL = "https://open.spotify.com/playlist/"
    SPOTIFY_URL_REGEX = re.compile(
        r"^https?:\/\/open.spotify.com\/user\/(?P<id>(?:(?!\?).)*).*$"
    )
    """A pattern to match user profile URLs.

    e.g. https://open.spotify.com/user/uwv4xcjfd79as24pcpckc9grb?si=c1c4d421a1f54b93
    """

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
            await self.bot.spotify.user.get_one(spotify_id)
        except SpotifyAPIError as e:
            if e.get_json().get("error", {}).get("status") == NOT_FOUND:
                embed = Embed(
                    title="Spotify User Not Found",
                    description="The Spotify user you provided was not found.",
                )
                await inter.send(embed=embed, ephemeral=True)
                return
            raise
        user = await User.objects().get_or_create(User.id == inter.user.id)
        await User.update({User.spotify_id: spotify_id}).where(User.id == user.id)

        embed = Embed(
            title="Linked to Spotify", description="Successfully linked to Spotify!"
        )
        await inter.send(embed=embed, ephemeral=True)

    @spotify.subcommand(name="unlink")
    async def spotify_unlink(self, inter: Inter) -> None:
        """Unlink your spotify account."""

        user = (
            await User.select(User.spotify_id).where(User.id == inter.user.id).first()
        )
        if user is None or user["spotify_id"] is None:
            raise NotLinked(self.bot)

        await User.update({User.spotify_id: None}).where(User.id == inter.user.id)

        embed = Embed(title="Unlinked", description="Your account has been unlinked.")
        await inter.send(embed=embed, ephemeral=True)

    @spotify.subcommand(name="playlists")
    async def spotify_playlists(self, inter: Inter) -> None:
        """List your spotify playlists."""

        user = await User.select().where(User.id == inter.user.id).first()
        if user is None:
            raise NotLinked(self.bot)

        user_id = user["spotify_id"]
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

        if playlist is None:
            return

        await self.bot.play(inter=inter, query=self.PLAYLIST_URL + playlist)


def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))
