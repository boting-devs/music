from __future__ import annotations

from time import gmtime, strftime
from typing import TYPE_CHECKING
from re import compile as re_compile

from botbase import CogBase, MyInter
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed


if TYPE_CHECKING:
    from vibr.player import Player


class Spotify(CogBase[Vibr]):
    SPOTIFY_URL_RE = re_compile(
        r"^https?:\/\/open.spotify.com\/user\/(?P<id>(?:(?!\?).)*).*$"
    )
    @slash_command(dm_permission=False)
    async def spotify(self,inter:MyInter,url:str) -> None:
        """Link your spotify account :)

        url:
            Your spotify profile url, find how to here: https://cdn.tooty.xyz/KSzS
        """
        match = self.SPOTIFY_URL_RE.match(url)
        
        if not match:
            embed = Embed(title="Invalid url",description="Please follow the instructions given below and use the command again.",
                          image="https://cdn.tooty.xyz/KSzS")
            return await inter.send(embed=embed)

        pass

def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))