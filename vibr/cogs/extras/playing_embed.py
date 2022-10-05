from __future__ import annotations

from logging import getLogger
from time import gmtime, strftime
from typing import TYPE_CHECKING

from botbase import MyInter as BBMyInter
from nextcord import Embed
from nextcord.utils import utcnow
from pomice import Playlist

from .types import MyInter

if TYPE_CHECKING:
    from pomice import Track


log = getLogger(__name__)


async def playing_embed(
    track: Track | Playlist,
    queue: bool = False,
    length: bool = False,
    save: bool = False,
    skipped_by: str | None = None,
    override_inter: MyInter | None = None,
):
    from . import views  # circular

    view = views.PlayButton()
    if isinstance(track, Playlist):
        assert track.tracks[0].ctx is not None

        inter: MyInter = track.tracks[0].ctx  # type: ignore

        title = track.name
        author = "Multiple Authors"
        time = strftime(
            "%H:%M:%S",
            gmtime(sum(t.length for t in track.tracks if t.length is not None) / 1000),
        )
    else:
        assert track.ctx is not None

        inter: MyInter = track.ctx  # type: ignore
        title = track.title
        author = track.author
        if not track.length:
            time = "Unknown"
        else:
            time = strftime(
                "%H:%M:%S",
                gmtime(track.length / 1000),
            )

    if override_inter:
        inter = override_inter

    embed = Embed(
        color=inter.bot.color,
        timestamp=utcnow(),
    )

    if length:
        if isinstance(track, Playlist):
            tr = track.tracks[0]
        else:
            tr = track

        c = inter.guild.voice_client.position
        assert tr.length is not None
        t = tr.length
        current = strftime("%H:%M:%S", gmtime(c // 1000))
        total = strftime("%H:%M:%S", gmtime(t // 1000))
        pos = round(c / t * 12)
        line = (
            ("\U00002501" * (pos - 1 if pos > 0 else 0))
            + "\U000025cf"
            + ("\U00002501" * (12 - pos))
        )
        # if 2/12, then get 1 before, then dot then 12 - 2 to pad to 12
        timing = f"{current} {line} {total}"
        embed.description = inter.user.mention + "\n" + timing
    elif save:
        embed.description = f"Song time: `{time}`"
    else:
        embed.description = f"{time} - {inter.user.mention}"

    if skipped_by:
        embed.description = embed.description + "\n skipped by " + skipped_by

    embed.set_author(
        name=str(title) + " - " + str(author),
        url=track.uri or "https://www.youtube.com/",
    )

    if inter.voice_client is not None:
        embed.set_footer(text=f"Volume : {inter.voice_client.volume}")

    if track.thumbnail:
        embed.set_thumbnail(url=track.thumbnail)

    if isinstance(inter, BBMyInter) and inter.response.is_done():
        ch = inter.channel
    else:
        ch = inter

    if queue:
        await ch.send(embed=embed, content="Queued", view=view)  # type: ignore
        # why on earth can that be a voice channel
    elif length:
        await ch.send(embed=embed, view=view)  # type: ignore
        # why on earth can that be a voice channel
    elif save:
        await inter.user.send(embed=embed)
    else:
        await ch.send(embed=embed, view=view)  # type: ignore
        # why on earth can that be a stage channel

        if isinstance(track, Playlist):
            # We do not need to log playlists, as we log the tracks.
            return

        # Try to insert, if there is already a record for this song+user, update.
        await inter.bot.db.execute(
            """INSERT INTO songs (id, spotify, member)
            VALUES ($1, $2, $3)
            ON CONFLICT (id, spotify, member)
            DO UPDATE SET
                amount = songs.amount + 1""",
            track.identifier,
            track.spotify,
            inter.user.id,
        )
        log.debug(
            "Added song %s to database for user %d", track.identifier, inter.user.id
        )
