from __future__ import annotations

import re

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter


class Spotify(CogBase[Vibr]):
    SPOTIFY_URL_RE = re.compile(
        r"^https?:\/\/open.spotify.com\/user\/(?P<id>(?:(?!\?).)*).*$"
    )

    @slash_command(dm_permission=False)
    async def spotify(self, inter: Inter, url: str) -> None:
        """Link your spotify account :)

        url:
            Your spotify profile url, find how to here: https://cdn.tooty.xyz/KSzS
        """
        match = self.SPOTIFY_URL_RE.match(url)

        if not match:
            embed = Embed(
                title="Invalid url",
                description="Please follow the instructions given below "
                "and use the command again.",
            )
            embed.set_image(url="https://cdn.tooty.xyz/KSzS")
            await inter.send(embed=embed)
            return


def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))
