# pyright: reportGeneralTypeIssues=false, reportPrivateImportUsage=false

from __future__ import annotations

from piccolo.columns import (
    M2M,
    Bytea,
    ForeignKey,
    Integer,
    LazyTableReference,
    Serial,
    Text,
    Timestamptz,
)
from piccolo.table import Table

from .user import User


class Song(Table):
    id = Serial(primary_key=True)
    lavalink_id = Bytea()
    likes = Integer(default=1)
    playlists = M2M(LazyTableReference("PlaylistToSong", module_path=__name__))


class Playlist(Table):
    id = Integer(primary_key=True, autoincrement=True)
    name = Text(default="Liked Songs")
    owner = ForeignKey(User, null=False)
    description = Text()
    songs = M2M(LazyTableReference("PlaylistToSong", module_path=__name__))


class PlaylistToSong(Table):
    id = Serial(primary_key=True)
    playlist = ForeignKey(Playlist)
    song = ForeignKey(Song)
    added = Timestamptz()
