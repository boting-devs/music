from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

from nextcord import Embed, SelectOption
from nextcord.ext.menus import ButtonMenuPages, PageSource
from nextcord.ui import Button, Select

from vibr.utils import truncate

if TYPE_CHECKING:
    from async_spotify.authentification import SpotifyAuthorisationToken

    from vibr.bot import Vibr
    from vibr.inter import Inter

    from ._types import PlaylistResponse, SpotifyPlaylist


FORMAT = "[**{name}**]({url}) by **{owner}** ({songs} songs)"


class PlaylistSource(PageSource):
    def __init__(
        self,
        *,
        initial: PlaylistResponse,
        token: SpotifyAuthorisationToken,
        bot: Vibr,
        per_page: int = 25,
    ) -> None:
        self.initial = initial["items"]
        self.total = initial["total"]
        self.token = token
        self.bot = bot
        self.per_page = per_page

    def is_paginating(self) -> bool:
        return self.total > self.per_page

    def get_max_pages(self) -> int | None:
        return ceil(self.total / self.per_page)

    async def get_page(self, page_number: int) -> list[SpotifyPlaylist]:
        if page_number == 0:
            return self.initial

        offset = page_number * self.per_page
        playlists = await self.bot.spotify.playlists.current_get_all(
            self.token, limit=self.per_page, offset=offset
        )
        return playlists["items"]

    async def format_page(
        self, menu: PlaylistMenu, entries: list[SpotifyPlaylist]
    ) -> Embed:
        # Hackish, the select injects itself.
        PlaylistSelect(entries, menu=menu)

        return Embed(
            title="Spotify Playlists",
            description="\n".join(
                self._get_playlist_description(playlist) for playlist in entries
            ),
            colour=self.bot.colour,
        )

    def _get_playlist_description(self, playlist: SpotifyPlaylist) -> str:
        return FORMAT.format(
            name=truncate(playlist["name"], length=50),
            url=playlist["external_urls"]["spotify"],
            owner=playlist["owner"]["display_name"] or "Unknown",
            songs=playlist["tracks"]["total"],
        )


class PlaylistMenu(ButtonMenuPages):
    ...


class PlaylistSelect(Select["PlaylistMenu"]):
    def __init__(self, playlists: list[SpotifyPlaylist], *, menu: PlaylistMenu) -> None:
        options = [self._create_option(playlist) for playlist in playlists]
        super().__init__(placeholder="Select a playlist", options=options)

        # Add select above menu buttons.
        children = menu.children.copy()
        for child in children:
            menu.remove_item(child)
        menu.add_item(self)
        for child in children:
            if isinstance(child, Button):
                menu.add_item(child)

    def _create_option(self, playlist: SpotifyPlaylist) -> SelectOption:
        description = (
            truncate(playlist["description"], length=100)
            if playlist["description"]
            else None
        )
        return SelectOption(
            label=playlist["name"],
            value=playlist["external_urls"]["spotify"],
            description=description,
        )

    async def callback(self, inter: Inter) -> None:
        assert self.view is not None
        assert inter.message is not None

        self.view.uri = self.values[0]
        await inter.message.delete()
        self.view.stop()
