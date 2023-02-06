from __future__ import annotations

from datetime import timedelta
from re import compile as re_compile
from typing import TYPE_CHECKING
from logging import getLogger

from nextcord import Guild, slash_command
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
log = getLogger(__name__)


class Config(Cog, name="config", description="Tweak around with the bot!"):
    SPOTIFY_URL_RE = re_compile(
        r"^https?:\/\/open.spotify.com\/user\/(?P<id>(?:(?!\?).)*).*$"
    )
    """A pattern to match user profile URLs.

    e.g. https://open.spotify.com/user/uwv4xcjfd79as24pcpckc9grb?si=c1c4d421a1f54b93
    """

    def __init__(self, bot: Vibr):
        self.bot = bot

    @property
    def emoji(self) -> str:
        return "🛠"

    @slash_command()
    async def spotify(self, ctx: MyInter, url: str):
        """Link your spotify account :)

        url:
            Your spotify profile url, find how to here: https://cdn.tooty.xyz/KSzS
        """

        # Check if input is a valid spotify account URL
        match = self.SPOTIFY_URL_RE.match(url)

        if not match:
            return await ctx.send_embed(
                "Invalid url",
                "find your spotify url with the format "
                "`https://open.spotify.com/users/<id>(?possible_extra)`",
                image="https://cdn.tooty.xyz/KSzS",
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
        log.debug("Linked spotify account %s to user %d", userid, ctx.author.id)

        await ctx.send_embed(
            "Linked!", f"your Discord has now been linked to {userid}", ephemeral=True
        )
    
    @slash_command()
    async def unlink(self,inter:MyInter):
        """Unlink Your spotify account"""
        h=await self.bot.db.fetchval(
            """SELECT spotify from users where id=$1""",inter.author.id,
        )
        if not h:
            return await inter.send_author_embed("Spotify Account is not linked",ephemeral=True)

        await self.bot.db.execute(
            """UPDATE users set spotify = NULL where id=$1""",inter.author.id,
        )
        self.bot.spotify_users[inter.author.id] = None

        await inter.send_embed("Delinked!","Your spotify account has been unlinked and deleted from the bot.",ephemeral=True)

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
