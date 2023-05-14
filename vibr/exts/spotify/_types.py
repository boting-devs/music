from __future__ import annotations

from typing import TypedDict


class PlaylistResponse(TypedDict):
    items: list[SpotifyPlaylist]
    total: int


class SpotifyPlaylist(TypedDict):
    name: str
    description: str
    owner: SpotifyUser
    external_urls: KnownURLs
    tracks: SpotifyTrackInfo


class KnownURLs(TypedDict):
    spotify: str


class SpotifyUser(TypedDict):
    display_name: str | None


class SpotifyTrackInfo(TypedDict):
    total: int
