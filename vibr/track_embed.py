from __future__ import annotations

from time import gmtime, strftime
from typing import TYPE_CHECKING

from mafic import Playlist

from vibr.embed import Embed
from vibr.utils import truncate

if TYPE_CHECKING:
    from mafic import Track

    from vibr.bot import Vibr


__all__ = ("track_embed",)


MAX_AUTHOR_LENGTH = 3
HTTP_FOUND = 302


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


async def track_embed(
    item: Track | Playlist,
    *,
    bot: Vibr,
    user: int,
    skipped: int | None = None,
    queued: bool = False,
    loop: bool = False,
    playnext:bool = False,
    playnow:bool = False,
) -> Embed:
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
    if skipped:
        embed = Embed(title=title)
        embed.add_field(name="Requested By", value=f"<@{user}>")
        embed.add_field(name="Skipped By", value=f"<@{skipped}>")
    else:
        embed = Embed(title=title, description=f"Requested by <@{user}>")

    embed.set_author(name=authors, url=url)
    if loop:
        embed.set_footer(text=f"Looping | Length: {track_time}")
    elif playnext:
        embed.set_footer(text=f"Playing Up Next | Length: {track_time}")
    elif playnow:
        embed.set_footer(text=f"Playing Now | Length: {track_time}")
    else:
        embed.set_footer(text="Queued | " * queued + f"Length: {track_time}")
    embed.set_thumbnail(url=thumbnail)

    return embed
