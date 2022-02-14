from __future__ import annotations

from asyncio import sleep
from os import getenv
from typing import TYPE_CHECKING

import nextcord
from botbase import MyContext
from nextcord import Guild, Message
from nextcord.ext.commands import command
from nextcord.ext.tasks import loop

if TYPE_CHECKING:
    from ..main import MyBot

class Misc(commands.Cog, name="misc", description="Meta commands about the bot!"):
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


    @command(help="Ping command", extras={"example": ".ping"})
    async def ping(self, ctx: MyContext):
        await ctx.send(f"🏓 Pong! `{round(self.bot.latency * 1000)} ms`")


    @command(help="invite link of bot")
    async def invite(self, ctx: MyContext):
        servers = list(self.bot.guilds)
        embed = nextcord.Embed(title="**Invite Link**", color=self.bot.color)
        embed.add_field(
            name=f"**The bot is currently in {str(len(servers))} servers**",
            value="**[invite me](https://discord.com/api/oauth2/authorize?client_id=882491278581977179&permissions=274885561408&scope=bot%20applications.commands&response_type=code&redirect_uri=https%3A%2F%2Fboting.xyz)**",
        )
        embed.set_image(url="https://learnenglishfunway.com/wp-content/uploads/2020/12/Music-2.jpg")
        await ctx.send(embed=embed)

    @command(
        help="Vibr support server link", extras={"example": ".support"}
    )
    async def support(self, ctx: MyContext):
        embed = nextcord.Embed(
            title="**Support Link**",
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
    bot.add_cog(Music(bot))
