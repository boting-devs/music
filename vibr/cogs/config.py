from __future__ import annotations

from datetime import timedelta
from re import compile as re_compile
from typing import TYPE_CHECKING

from nextcord import Guild, SlashOption, slash_command
from nextcord.ext.commands import Cog, command, is_owner
from nextcord.utils import format_dt, utcnow

from .extras.types import MyContext, MyInter

if TYPE_CHECKING:
    from ..__main__ import Vibr


urlprompt = """
Please send your spotify profile url to link your account to vibr.
(sizing and blur are for visual purposes only)
"""
TEST = [802586580766162964, 939509053623795732]


class Config(Cog, name="config", description="Tweak around with the bot!"):
    SPOTIFY_URL_RE = re_compile(
        r"^https?:\/\/open.spotify.com\/user\/(?P<id>(?:(?!\?).)*).*$"
    )

    def __init__(self, bot: Vibr):
        self.bot = bot

    @property
    def emoji(self) -> str:
        return "🛠"

    @slash_command()
    async def spotify(
        self,
        ctx: MyInter,
        url: str = SlashOption(
            description="Your spotify profile url, find how to here: https://cdn.tooty.xyz/KSzS"
        ),
    ):
        """Link your spotify account :)"""

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

        await ctx.send_embed(
            "Linked!", f"your Discord has now been linked to {userid}", ephemeral=True
        )

    @is_owner()
    @command(hidden=True)
    async def whitelist(self, ctx: MyContext, guild: Guild, forever: bool = False):
        if forever:
            time = utcnow() + timedelta(weeks=9999)
        else:
            time = utcnow() + timedelta(weeks=1)

        await self.bot.db.execute(
            """INSERT INTO guilds (id, whitelisted) 
            VALUES ($1, $2) 
            ON CONFLICT (id) DO UPDATE 
                SET whitelisted=$2""",
            guild.id,
            time,
        )
        self.bot.whitelisted_guilds[guild.id] = time
        await ctx.send(f"Whitelisted until {format_dt(time)}")


def setup(bot: Vibr):
    bot.add_cog(Config(bot))
