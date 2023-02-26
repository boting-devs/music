from __future__ import annotations

from time import gmtime, strftime

from botbase import CogBase, MyInter
from mafic import Player, Playlist, SearchType, Track
from nextcord import ApplicationCommandType, SlashOption, slash_command
from nextcord.utils import get

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.utils import truncate

from ._errors import NoTracksFound

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

    async with bot.session.get(
        f"https://odesli.co/{track.uri.replace('://', ':/')}", allow_redirects=False
    ) as response:
        if response.status == HTTP_FOUND:
            loc = response.headers.get("Location", track.uri)
            if loc != "/not-found":
                return loc

        return None


class Play(CogBase[Vibr]):
    SEARCH_TYPE = SlashOption(
        name="search-type",
        choices={
            "Default": SearchType.YOUTUBE.value,
            "SoundCloud": SearchType.SOUNDCLOUD.value,
            "Spotify": SearchType.SPOTIFY_SEARCH.value,
            "Apple Music": SearchType.APPLE_MUSIC.value,
            "Deezer": SearchType.DEEZER_ISRC.value,
            "Yandex Music": SearchType.YANDEX_MUSIC,
        },
        default=SearchType.YOUTUBE.value,
    )

    @slash_command(dm_permission=False)
    async def play(
        self,
        inter: MyInter,
        query: str,
        search_type: str = SEARCH_TYPE,
    ) -> None:
        """Play a link, query or past song.

        query:
            Can be a URL/link, query or past played song.
        search_type:
            The platform to search if this is a query.
        """

        assert inter.guild is not None

        if not inter.guild.voice_client:
            commands = self.bot.get_all_application_commands()
            join = get(commands, name="join", type=ApplicationCommandType.chat_input)
            if not join:
                raise RuntimeError

            await join(inter)

        await inter.response.defer()

        player: Player = (
            inter.guild.voice_client
        )  # pyright: ignore[reportGeneralTypeIssues]

        result = await player.fetch_tracks(
            query=query, search_type=SearchType(search_type)
        )

        if not result:
            raise NoTracksFound

        if isinstance(result, Playlist):
            track = result.tracks[0]
            title = result.name
            authors = get_authors(result.tracks)
            length = sum(track.length for track in result.tracks)
            strftime("%H:%M:%S", gmtime(length / 1000))
            url = None
            thumbnail = "http://clipground.com/images/tone-duration-clipart-16.jpg"
        else:
            track = result[0]
            title = track.title
            authors = track.author
            length = track.length
            strftime("%H:%M:%S", gmtime(length / 1000))
            url = await get_url(track, bot=self.bot)

            source = track.source

            # Wait for lavalink v4 for missing sources tbh.
            # Soundcloud, Spotify, Deezer and a few others just take one API req
            # to get the thumbnail, but Lavalink does that already.
            if source == "youtube":
                thumbnail = (
                    f"https://img.youtube.com/vi/{track.identifier}/mqdefault.jpg"
                )
            else:
                thumbnail = "http://clipground.com/images/tone-duration-clipart-16.jpg"

        embed = Embed(title=title)
        embed.set_author(name=authors, url=url)
        embed.set_footer(text=f"Length: {length}")
        embed.set_thumbnail(url=thumbnail)

        await player.play(track)

        await inter.followup.send(embed=embed)  # pyright: ignore


def setup(bot: Vibr) -> None:
    bot.add_cog(Play(bot))
