from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from botbase import CogBase
from nextcord import slash_command
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter

from .playing._errors import LyricsNotFound, SongNotProvided

if TYPE_CHECKING:
    from vibr.player import Player

log = getLogger(__name__)


class Lyrics(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    async def lyrics(self, inter: Inter, query: str | None = None) -> None:
        """Get Song's Lyrics
        query:
            The song to search lyrics for, do not input if you want the current song."""

        player: Player = inter.guild.voice_client
        if not query:
            if player is None or player.current is None:
                raise SongNotProvided

            assert player.current.title is not None
            q = player.current.title
        else:
            q = query

        a = await inter.send("`Searching....`")


        url_search = f"https://api.flowery.pw/v1/lyrics/search?query={q}"

        async with self.bot.session.get(url_search) as resp:
            result = await resp.json()
        try:
            isrc = result["tracks"][0]["external"]["isrc"]
            spotify_id = result["tracks"][0]["external"]["spotify_id"]
        except KeyError:
            await a.delete()
            raise LyricsNotFound

        url_lyrics = f"https://api.flowery.pw/v1/lyrics?isrc={isrc}&spotify_id={spotify_id}&query={q}"

        async with self.bot.session.get(url_lyrics) as res:
            lyrics = await res.json()


        try:
            lyrics_text = lyrics["lyrics"]["text"]
            title = lyrics["track"]["title"]
            artist = lyrics["track"]["artist"]
            thumbnail = lyrics["track"]["media"]["artwork"]
        except KeyError:
            await a.delete()
            raise LyricsNotFound

        embed = Embed(title=title, description=lyrics_text, timestamp=utcnow())
        embed.set_author(name=artist)
        embed.set_thumbnail(url=thumbnail)
        await a.edit(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Lyrics(bot))
