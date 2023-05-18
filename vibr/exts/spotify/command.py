from __future__ import annotations

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

from ._errors import NotLinked
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

        # signed_user_id = self.serializer.dumps(inter.user.id)
        # url = f"{self.AUTHORIZE_URL}/?user={signed_user_id}"

        # embed = Embed(
        #     title="Link Your Spotify Account", description=f"[Click here]({url})"
        # )
        # await inter.send(embed=embed, ephemeral=True)

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
