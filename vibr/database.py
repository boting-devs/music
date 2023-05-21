from __future__ import annotations

from base64 import b64decode
from typing import TYPE_CHECKING

from botbase.db import database

from vibr.db import Playlist, Song, User

if TYPE_CHECKING:
    import nextcord
    from mafic import Track
    from nextcord import Member


@database.transaction()
async def add_to_liked(*, user: nextcord.User | Member, track: Track) -> None:
    await User.objects.create(id=user.id)

    # represent_as_base64_str means this cant use str itself since
    # it is only converted by ormar on `__get__` and `__set__`.
    data, created = await Song.objects.get_or_create(lavalink_id=b64decode(track.id))
    if not created:
        data.likes += 1
        await data.update()

    playlist, created = await Playlist.objects.get_or_create(
        name="Liked Songs", owner=user.id
    )

    await playlist.songs.add(data)
