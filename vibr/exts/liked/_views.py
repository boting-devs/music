from __future__ import annotations

from base64 import b64encode
from math import ceil
from time import gmtime, strftime
from typing import TYPE_CHECKING

from nextcord.ext.menus import ButtonMenuPages, PageSource

from vibr.db import Playlist, PlaylistToSong
from vibr.embed import Embed
from vibr.utils import truncate

if TYPE_CHECKING:
    from mafic import Track

    from vibr.bot import Vibr


FORMAT = "**{index}.** [**{title}**]({uri}) by **{author}** [{length}]"


class LikedSource(PageSource):
    def __init__(
        self,
        *,
        playlist: Playlist,
        count: int,
        bot: Vibr,
        per_page: int = 25,
    ) -> None:
        self.playlist = playlist
        self.per_page = per_page
        self.count = count
        self.bot = bot

    def is_paginating(self) -> bool:
        return self.count > self.per_page

    def get_max_pages(self) -> int | None:
        return ceil(self.count / self.per_page)

    async def get_page(self, page_number: int) -> list[tuple[Track, int]]:
        songs = (
            await PlaylistToSong.select(PlaylistToSong.song.lavalink_id)
            .where(PlaylistToSong.playlist == self.playlist.id)
            .offset(page_number * self.per_page)
            .limit(self.per_page)
            .order_by(PlaylistToSong.added)
        )
        node = self.bot.pool.label_to_node["LOCAL"]
        return list(
            zip(
                await node.decode_tracks(
                    [b64encode(song["song.lavalink_id"]).decode() for song in songs]
                ),
                range(
                    page_number * self.per_page,
                    page_number * self.per_page + self.per_page,
                ),
                # Page may not be full.
                strict=False,
            )
        )

    async def format_page(
        self, _: LikedMenu, entries: list[tuple[Track, int]]
    ) -> Embed:
        return Embed(
            title="Liked Songs",
            description="\n".join(
                self._get_track_description(track, index) for track, index in entries
            ),
        )

    def _get_track_description(self, track: Track, index: int) -> str:
        return FORMAT.format(
            index=index + 1,
            title=truncate(track.title, length=50),
            author=truncate(track.author, length=50),
            uri=track.uri,
            length=strftime("%H:%M:%S", gmtime((track.length or 0) / 1000)),
        )


class LikedMenu(ButtonMenuPages):
    ...
