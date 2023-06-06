from __future__ import annotations

from typing import TypedDict


class PlaylistResponse(TypedDict):
    items: list[SpotifyPlaylist]
    total: int


class TracksResponse(TypedDict):
    items: list[SpotifyTrack]
    total: int


class SpotifyPlaylist(TypedDict):
    id: str
    name: str
    description: str
    owner: SpotifyUser
    external_urls: KnownURLs
    tracks: SpotifyTrackData
    images: list[SpotifyImage]


class SpotifyTrack(TypedDict):
    is_local: bool
    track: SpotifyTrackInfo


class SpotifyTrackInfo(TypedDict):
    external_urls: KnownURLs
    id: str
    name: str
    artists: list[SpotifyArtist]
    external_ids: ExternalIDs
    images: list[SpotifyImage]
    duration_ms: int
    album: SpotifyAlbum


class SpotifyAlbum(TypedDict):
    images: list[SpotifyImage]


class SpotifyImage(TypedDict):
    url: str


class SpotifyArtist(TypedDict):
    name: str


class ExternalIDs(TypedDict):
    isrc: str


class KnownURLs(TypedDict):
    spotify: str


class SpotifyUser(TypedDict):
    display_name: str | None


class SpotifyTrackData(TypedDict):
    total: int
