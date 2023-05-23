from __future__ import annotations

import functools
from base64 import b64decode, b64encode
from typing import TYPE_CHECKING, ParamSpec, TypeVar, cast

from asyncpg import UniqueViolationError

from vibr.db import Playlist, Song, User
from vibr.db.playlists import PlaylistToSong

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    import nextcord
    from mafic import Track
    from nextcord import Member
    from piccolo.columns import ForeignKey
    from piccolo.engine.postgres import PostgresTransaction

P = ParamSpec("P")
T = TypeVar("T")


def transaction(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    @functools.wraps(func)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        db = User._meta.db
        async with cast("PostgresTransaction", db.transaction()):
            return await func(*args, **kwargs)

    return wrapped


@transaction
async def add_to_liked(*, user: nextcord.User | Member, track: Track) -> bool:
    # song = (
    #     await Song.insert(
    #         Song({Song.lavalink_id: b64decode(track.id)}),
    #     )
    #     .on_conflict(
    #         (Song.id),
    #         "DO UPDATE",
    #         ((Song.likes, Unquoted("song.likes + 1")),),
    #     )
    #     .returning(*Song.all_columns())
    # )[0]
    try:
        song = Song.from_dict(
            (
                await Song.insert(
                    Song({Song.lavalink_id: b64decode(track.id)})
                ).returning(*Song.all_columns())
            )[0]
        )
        song._exists_in_db = True
    except UniqueViolationError:
        song = cast(
            Song, await Song.objects().get(Song.lavalink_id == b64decode(track.id))
        )
        song.likes += 1
        await song.update()

    owner = await User.objects().get_or_create(User.id == user.id)
    playlist = await Playlist.objects().get_or_create(
        (Playlist.name == "Liked Songs") & (Playlist.owner.id == owner.id),
        defaults={
            Playlist.owner: owner,
        },
    )

    try:
        await playlist.add_m2m(song, m2m=Playlist.songs)
    except UniqueViolationError:
        return True

    return False


@transaction
async def remove_from_liked(*, user: nextcord.User | Member, index: int) -> str | None:
    playlist_to_song = (
        await PlaylistToSong.objects(PlaylistToSong.song, PlaylistToSong.playlist)
        .where(
            (cast("ForeignKey", PlaylistToSong.playlist.owner).id == user.id)
            & (PlaylistToSong.playlist.name == "Liked Songs")
        )
        .offset(index)
        .limit(1)
        .order_by(PlaylistToSong.added)
        .first()
    )
    if playlist_to_song is None:
        return None

    song = playlist_to_song.song
    playlist = playlist_to_song.playlist

    if song is None:
        return None

    await playlist.remove_m2m(song, m2m=Playlist.songs)

    song.likes -= 1
    if song.likes == 0:
        await song.remove()
    else:
        await song.save()

    return b64encode(song.lavalink_id).decode()
