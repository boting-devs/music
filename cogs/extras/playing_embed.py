from __future__ import annotations

from typing import TYPE_CHECKING
from time import gmtime, strftime

from pomice import Playlist
from nextcord import Embed
from nextcord.utils import utcnow

from . import views
from .types import MyInter, MyContext

if TYPE_CHECKING:
    from pomice import Track


async def playing_embed(
    track: Track | Playlist,
    queue: bool = False,
    length: bool = False,
    skipped_by: str | None = None,
    override_ctx: MyContext | MyInter | None = None,
):
    view = views.PlayButton()
    if isinstance(track, Playlist):
        assert track.tracks[0].ctx is not None

        ctx: MyContext | MyInter = track.tracks[0].ctx  # type: ignore

        title = track.name
        author = "Multiple Authors"
        time = strftime(
            "%H:%M:%S",
            gmtime(sum(t.length for t in track.tracks if t.length is not None) / 1000),
        )
    else:
        assert track.ctx is not None

        ctx: MyContext | MyInter = track.ctx  # type: ignore
        title = track.title
        author = track.author
        if not track.length:
            time = "Unknown"
        else:
            time = strftime(
                "%H:%M:%S",
                gmtime(track.length / 1000),
            )

    if override_ctx:
        ctx = override_ctx

    embed = Embed(
        color=ctx.bot.color,
        timestamp=utcnow(),
    )

    if length:
        if isinstance(track, Playlist):
            tr = track.tracks[0]
        else:
            tr = track

        c = ctx.voice_client.position
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
        embed.description = ctx.author.mention + "\n" + timing
    else:
        embed.description = f"{time} - {ctx.author.mention}"

    if skipped_by:
        embed.description = embed.description + "\n skipped by " + skipped_by

    embed.set_author(
        name=str(title) + " - " + str(author),
        url=track.uri or "https://www.youtube.com/",
    )

    if track.thumbnail:
        embed.set_thumbnail(url=track.thumbnail)

    if isinstance(ctx, MyInter) and ctx.response.is_done():
        ch = ctx.channel
    else:
        ch = ctx

    print(isinstance(ctx, MyInter))
    if isinstance(ctx, MyInter):
        print(ctx.response.is_done())
        print(id(ctx))
        print(id(ctx.response))

    if queue:
        await ch.send(embed=embed, content="Queued", view=view)  # type: ignore
        # why on earth can that be a voice channel
    elif length:
        await ch.send(embed=embed, view=view)  # type: ignore
        # why on earth can that be a voice channel
    else:
        await ch.send(embed=embed, view=view)  # type: ignore
        # why on earth can that be a voice channel

        if isinstance(track, Playlist):
            return

        await ctx.bot.db.execute(
            """INSERT INTO songs (id, spotify, member) 
            VALUES ($1, $2, $3) 
            ON CONFLICT (id, spotify, member)
            DO UPDATE SET
                amount = songs.amount + 1""",
            track.identifier,
            track.spotify,
            ctx.author.id,
        )
