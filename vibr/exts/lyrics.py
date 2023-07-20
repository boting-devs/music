from __future__ import annotations

from logging import getLogger

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import voted
from vibr.inter import Inter

log = getLogger(__name__)


class Lyrics(CogBase[Vibr]):
    @slash_command()
    @voted
    async def lyrics(self, inter: Inter, query: str | None = None) -> None:
        """Get a song's lyrics

        query:
            The song to search lyrics for, leave blank if you want the current song.
        """

        await self.bot.lyrics(inter=inter, song=query)


def setup(bot: Vibr) -> None:
    bot.add_cog(Lyrics(bot))
