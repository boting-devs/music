from __future__ import annotations

from datetime import UTC, datetime
from os import environ
from typing import TYPE_CHECKING, cast

from botbase import CogBase
from itsdangerous import URLSafeSerializer
from nextcord import slash_command
from ormar import NoMatch

from vibr.bot import Vibr
from vibr.db import User
from vibr.embed import Embed
from vibr.inter import Inter

from ._views import PlaylistMenu, PlaylistSource

if TYPE_CHECKING:
    from ._types import PlaylistResponse


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
        await menu.start(interaction=inter)


def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))
