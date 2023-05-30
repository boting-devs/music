from __future__ import annotations

import re
from time import gmtime, strftime
from typing import TYPE_CHECKING

from mafic import Playlist, Track
from nextcord.utils import escape_markdown

from vibr.db import SongLog
from vibr.embed import Embed
from vibr.inter import Inter
from vibr.utils import truncate

from . import buttons

if TYPE_CHECKING:
    from vibr.bot import Vibr


__all__ = ("track_embed",)


MAX_AUTHOR_LENGTH = 3
HTTP_FOUND = 302
BANDCAMP_TRACK = "https://chordorchard.bandcamp.com/track/"
DISCORD_ATTACHMENT_RE = re.compile(
    r"https?://cdn\.discordapp\.com/attachments/"
    r"((?:[0-9]+)/(?:[0-9]+)/(?:[a-zA-Z0-9_.]+)+)",
)
SOUNDCLOUD_TRACK = "https://soundcloud.com/"
VIMEO_VIDEO = "https://vimeo.com/"


def get_authors(tracks: list[Track]) -> str:
    """Get a string of authors.

    Parameters
    ----------
    tracks:
        The list of tracks to parse.

    Returns
    -------
    str
        The string of authors, or ``"Multiple Authors"``
        if more than ``MAX_AUTHOR_LENGTH``.
    """

    authors = {track.author for track in tracks}
    if len(authors) > MAX_AUTHOR_LENGTH:
        return "Multiple Authors"

    return truncate(", ".join(authors), length=256)


async def get_url(track: Track, *, bot: Vibr) -> str | None:
    """Get a URL to Odesli, or just the URL if not found.

    Parameters
    ----------
    track:
        The Mafic track to get the URI from.
    bot:
        The bot object to get the session from.
    """

    if not track.uri:
        return None

    del bot

    return track.uri

    # FIXME: not sure about the speed of this,
    # maybe we can use our own url and have this fetching happen there?

    # async with bot.session.get(
    #     f"https://odesli.co/{track.uri.replace('://', ':/')}", allow_redirects=False
    # ) as response:
    #     if response.status == HTTP_FOUND:
    #         loc = response.headers.get("Location", track.uri)
    #         if loc != "/not-found":
    #             return loc

    #     return None


SIMPLE_SOURCES = {
    "applemusic": SongLog.Type.APPLE_MUSIC,
    "deezer": SongLog.Type.DEEZER,
    "spotify": SongLog.Type.SPOTIFY,
    "youtube": SongLog.Type.YOUTUBE,
}


def get_type_and_identifier(track: Track) -> tuple[str, int]:  # noqa: PLR0911
    assert track.uri is not None

    if track.source == "bandcamp":
        return track.uri.removeprefix(BANDCAMP_TRACK), SongLog.Type.BANDCAMP.value

    if track.source == "http":
        if match := DISCORD_ATTACHMENT_RE.match(track.uri):
            return match.group(1), SongLog.Type.DISCORD.value

        return track.uri, SongLog.Type.OTHER.value

    if track.source == "soundcloud":
        return track.uri.removeprefix(SOUNDCLOUD_TRACK), SongLog.Type.SOUNDCLOUD.value

    # I do not think Twitch works right now.

    if track.source == "vimeo":
        return track.uri.removeprefix(VIMEO_VIDEO), SongLog.Type.VIMEO.value

    if track.source in SIMPLE_SOURCES:
        return track.identifier, SIMPLE_SOURCES[track.source].value

    return track.uri, SongLog.Type.OTHER.value


async def track_embed(
    item: Track | Playlist,
    *,
    bot: Vibr,
    user: int,
    inter: Inter | None = None,
    skipped: int | None = None,
    queued: int | None = None,
    looping: bool = False,
    next: bool = False,
    length_embed: bool = False,
    grabbed: bool = False,
) -> tuple[Embed, buttons.PlayButtons]:
    view = buttons.PlayButtons(item)

    if isinstance(item, Playlist):
        title = item.name
        authors = get_authors(item.tracks)
        length = sum(track.length for track in item.tracks)
        track_time = strftime("%H:%M:%S", gmtime(length / 1000))
        url = None
        thumbnail = item.plugin_info.get(
            "artworkUrl", "http://clipground.com/images/tone-duration-clipart-16.jpg"
        )
    else:
        title = item.title
        authors = item.author
        length = item.length
        track_time = strftime("%H:%M:%S", gmtime(length / 1000))
        url = await get_url(item, bot=bot)
        thumbnail = (
            item.artwork_url
            or "http://clipground.com/images/tone-duration-clipart-16.jpg"
        )

    title = escape_markdown(title)

    if skipped:
        embed = Embed(title=title)
        embed.add_field(name="Requested By", value=f"<@{user}>")
        embed.add_field(name="Skipped By", value=f"<@{skipped}>")
    if grabbed:
        embed = Embed(title=title)
    else:
        embed = Embed(title=title, description=f"Requested by <@{user}>")

    if length_embed:
        tr = item.tracks[0] if isinstance(item, Playlist) else item

        assert inter is not None
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
        embed.description = timing

    embed.set_author(name=authors, url=url)

    if looping:
        embed.set_footer(text=f"Looping | Length: {track_time}")
    elif next:
        embed.set_footer(text=f"Playing Up Next | Length: {track_time}")
    elif queued:
        embed.set_footer(
            text=f"Queued - {queued} | " * bool(queued) + f"Length: {track_time}"
        )
    else:
        embed.set_footer(text=f"Length: {track_time}") 
    embed.set_thumbnail(url=thumbnail)

    if not grabbed and isinstance(item, Track):
        await SongLog.raw(
            """INSERT INTO song_log (identifier, type, user_id)
            VALUES ({}, {}, {})
            ON CONFLICT (type, identifier, user_id)
            DO UPDATE SET
                amount = song_log.amount + 1
            """,
            *get_type_and_identifier(item),
            user,
        )

    return embed, view
