from __future__ import annotations

from base64 import b64decode
from typing import TYPE_CHECKING

from asyncpg import UniqueViolationError
from botbase.db import database

from vibr.db import Playlist, Song, User

if TYPE_CHECKING:
    import nextcord
    from mafic import Track
    from nextcord import Member


@database.transaction()
async def add_to_liked(*, user: nextcord.User | Member, track: Track) -> bool:
    await User.objects.get_or_create(id=user.id)

    # represent_as_base64_str means this cant use str itself since
    # it is only converted by ormar on `__get__` and `__set__`.
    data, created = await Song.objects.get_or_create(lavalink_id=b64decode(track.id))
    if not created:
        data.likes += 1
        await data.update()

    playlist, created = await Playlist.objects.get_or_create(
        name="Liked Songs", owner=user.id
    )

    try:
        await playlist.songs.add(data)
    except UniqueViolationError:
        return True

    return False


@database.transaction()
async def remove_from_liked(*, user: nextcord.User | Member, index: int) -> str | None:
    playlist = (
        await Playlist.objects.select_related(["songs"])
        .filter(owner=user.id, name="Liked Songs")
        .offset(index, limit_raw_sql=True)
        .limit(1, limit_raw_sql=True)
        .order_by("playlisttosong__added")
        .get_or_none()
    )
    if playlist is None:
        return None

    if not playlist.songs:
        return None

    song = playlist.songs[0]
    await playlist.songs.remove(song)

    song.likes -= 1
    if song.likes == 0:
        await song.delete()
    else:
        # Apparently ormar forgor I wanted it to be a str but store as bytes.
        # So I have to do it myself.
        song.lavalink_id = song.lavalink_id
        await song.update()

    return song.lavalink_id
