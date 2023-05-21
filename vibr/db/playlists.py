# pyright: reportGeneralTypeIssues=false, reportPrivateImportUsage=false

from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import BaseMeta
from nextcord.utils import utcnow
from ormar import DateTime, ForeignKey, Integer, LargeBinary, ManyToMany, Model, Text
from sqlalchemy import UniqueConstraint

from .user import User

if TYPE_CHECKING:
    from datetime import datetime


class Song(Model):
    class Meta(BaseMeta):
        tablename = "songs"

    id: int = Integer(primary_key=True, autoincrement=True)
    lavalink_id: str = LargeBinary(max_length=300, represent_as_base64_str=True)
    likes: int = Integer(default=0)


class PlaylistToSong(Model):
    class Meta(BaseMeta):
        tablename = "playlists_to_songs"
        # This is in the migration, but cannot be done easily with ormar :(
        # constraints = [UniqueConstraint("song", "playlist")]

    # This is not the real primary key, just to appease ormar. I wanna use piccolo :(
    added: datetime = DateTime(timezone=True, default=utcnow, primary_key=True)


class Playlist(Model):
    class Meta(BaseMeta):
        tablename = "playlists"
        constraints = [UniqueConstraint("name", "owner")]

    id: int = Integer(primary_key=True, autoincrement=True)
    name: str = Text(default="Liked Songs")
    owner: int = ForeignKey(
        User, related_name="playlists", ondelete="CASCADE", nullable=False
    )
    description: str = Text(default="")
    songs = ManyToMany(Song, through=PlaylistToSong)
