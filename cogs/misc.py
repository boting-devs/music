from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from nextcord import ButtonStyle, ClientUser, Embed, Interaction, Member, User
from nextcord.ext.commands import (
    BotMissingPermissions,
    Cog,
    Context,
    MissingRequiredArgument,
    NoPrivateMessage,
    check,
    command,
)
from nextcord.ext.menus import ButtonMenuPages, ListPageSource
from nextcord.utils import utcnow

from .extras.errors import NotConnected, NotInVoice, TooManyTracks, LyricsNotFound
from .extras.types import MyContext

if TYPE_CHECKING:
    from ..mmain import MyBot

class Misc(Cog, name="misc", description="Meta commands about the bot!"):
    def __init__(self, bot: MyBot):
        self.bot = bot

    def cog_check(self, ctx: MyContext) -> bool:
        assert ctx.command is not None
        if ctx.command.extras.get("bypass"):
            return True

        if (
            ctx.guild is None
            or isinstance(ctx.author, User)
            or isinstance(ctx.me, ClientUser)
        ):
            raise NoPrivateMessage()

        return True
    @property
    def emoji(self) -> str:
        return "⚙️"

    @command(help="Ping command", extras={"example": ".ping"})
    async def ping(self, ctx: MyContext):
        await ctx.send(f"🏓 Pong! `{round(self.bot.latency * 1000)} ms`")


    @command(help="invite link of bot")
    async def invite(self, ctx: MyContext):
        servers = list(self.bot.guilds)
        embed = Embed(title="**Invite Link**", color=self.bot.color)
        embed.add_field(
            name=f"**The bot is currently in {str(len(servers))} servers**",
            value="**[invite me](https://discord.com/api/oauth2/authorize?client_id=882491278581977179&permissions=274919115840&scope=bot)**",
        )
        embed.set_image(url="https://learnenglishfunway.com/wp-content/uploads/2020/12/Music-2.jpg")
        await ctx.send(embed=embed)

    @command(
        help="Vibr support server link", extras={"example": ".support"}
    )
    async def support(self, ctx: MyContext):
        embed = Embed(
            title="**Support Link**",
            color=self.bot.color
        )
        embed.add_field(
            name="**Facing any problem? Join the support server**",
            value="**[click here](https://discord.gg/v3UvgPXwHq)**",
        )
        embed.set_image(
            url="https://c.tenor.com/lhlDEs5fNNEAAAAC/music-beat.gif"
        )
        await ctx.send(embed=embed)

def setup(bot: MyBot):
    bot.add_cog(Misc(bot))
