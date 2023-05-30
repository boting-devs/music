from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter
from vibr.utils import truncate

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

        await self.bot.lyrics(inter=inter, query=query)


def setup(bot: Vibr) -> None:
    bot.add_cog(Lyrics(bot))
