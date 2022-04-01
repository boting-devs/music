from __future__ import annotations

from typing import TypedDict

import botbase
import pomice
import nextcord


class Player(pomice.Player):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.queue: list[pomice.Track] = []


class MyContext(botbase.MyContext):
    voice_client: Player
    guild: FakeGuild


class FakeGuild(nextcord.Guild):
    voice_client: Player


class MyInter(botbase.MyInter):
    guild: FakeGuild
    voice_client: Player


class SpotifyPlaylists(TypedDict):
    href: str
    items: list[Playlist]
    limit: int
    next: str | None
    offset: int
    previous: str | None
    total: int


class Playlist(TypedDict):
    url: str
    type: str
    tracks: list[Track]
    snapshot_id: str
    public: bool
    owner: SpotifyUser
    name: str
    images: list[Image]
    id: str
    href: str
    followers: Followers
    external_urls: ExtUrl
    description: str | None
    collaborative: bool


class Image(TypedDict):
    width: int
    height: int
    url: str


class Track(TypedDict):
    total: int
    previous: str | None
    offset: str
    next: str | None
    limit: int
    items: list[dict]
    href: str


class SpotifyUser(TypedDict):
    display_name: str
    uri: str
    type: str
    id: str
    href: str
    followers: Followers


class Followers(TypedDict):
    href: str
    total: int
    external_urls: ExtUrl


class ExtUrl(TypedDict):
    spotify: str
