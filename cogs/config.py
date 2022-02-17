from __future__ import annotations

from re import compile as re_compile
from typing import TYPE_CHECKING

from nextcord.ext.commands import Cog, command

from .extras.types import MyContext

if TYPE_CHECKING:
    from ..mmain import MyBot


urlprompt = """
Please send your spotify profile url to link your account to vibr.
(sizing and blur are for visual purposes only)
"""


class Config(Cog, name="config", description="Tweak around with the bot!"):
    SPOTIFY_URL_RE = re_compile(
        r"^https?:\/\/open.spotify.com\/user\/(?P<id>(?:(?!\?).)*).*$"
    )

    def __init__(self, bot: MyBot):
        self.bot = bot

    @command(help="Link up your cool Spotify account :)")
    async def spotify(self, ctx: MyContext):
        await ctx.send_embed(description=urlprompt, image="https://cdn.tooty.xyz/KSzS")

        m = await self.bot.wait_for(
            "message",
            check=lambda m: m.author.id == ctx.author.id
            and m.channel.id == ctx.channel.id,
        )
        url = m.content

        match = self.SPOTIFY_URL_RE.match(url)

        if not match:
            return await ctx.send_embed(
                "Invalid url",
                "find your spotify url with the format "
                "`https://open.spotify.com/users/<id>(?possible_extra)`",
            )

        userid = match.group("id")

        await self.bot.db.execute(
            """INSERT INTO users (id, spotify) 
            VALUES ($1, $2) 
            ON CONFLICT (id) DO UPDATE SET 
                spotify=$2""",
            ctx.author.id,
            userid,
        )
        self.bot.spotify_users[ctx.author.id] = userid

        await ctx.send_embed("Linked!", f"your Discord has now been linked to {userid}")


def setup(bot: MyBot):
    bot.add_cog(Config(bot))
