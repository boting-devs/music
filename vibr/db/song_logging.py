from __future__ import annotations

from enum import Enum

from piccolo.columns import BigInt, Integer, Serial, SmallInt, Text
from piccolo.table import Table


class SongLog(Table):
    class Type(Enum):
        BANDCAMP = 0
        DISCORD = 1
        SOUNDCLOUD = 2
        TWITCH = 3
        VIMEO = 4
        YOUTUBE = 5
        APPLE_MUSIC = 6
        DEEZER = 7
        SPOTIFY = 8
        OTHER = 9

    id = Serial(primary_key=True)
    type = SmallInt(default=Type.OTHER, choices=Type)
    identifier = Text()
    user_id = BigInt()
    amount = Integer()
