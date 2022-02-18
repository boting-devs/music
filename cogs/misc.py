from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord import Embed
from nextcord.ext.commands import (
    Cog,
    command,
    MissingPermissions
)

from .extras.types import MyContext

if TYPE_CHECKING:
    from ..mmain import MyBot


class Misc(Cog, name="misc", description="Meta commands about the bot!"):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @property
    def emoji(self) -> str:
        return "⚙️"

    @command(help="Ping command")
    async def ping(self, ctx: MyContext):
        await ctx.send(f"🏓 Pong! `{round(self.bot.latency * 1000)} ms`")

    @command(help="invite link of bot")
    async def invite(self, ctx: MyContext):
        servers = list(self.bot.guilds)
        embed = Embed(title="**Invite Link**", color=self.bot.color)
        embed.add_field(
            name=f"**The bot is currently in {len(servers)} servers**",
            value="**[invite me](https://discord.com/api/oauth2/authorize?"
                  "client_id=882491278581977179&permissions=274919115840&scope=bot"
                  "%20applications.commands)**",
        )
        embed.set_image(
            url="https://learnenglishfunway.com/wp-content/uploads/2020/12/Music-2.jpg"
        )
        await ctx.send(embed=embed)

    @command(help="Vibr support server link")
    async def support(self, ctx: MyContext):
        embed = Embed(title="**Support Link**", color=self.bot.color)
        embed.add_field(
            name="**Facing any problem? Join the support server**",
            value="**[click here](https://discord.gg/v3UvgPXwHq)**",
        )
        embed.set_image(url="https://c.tenor.com/lhlDEs5fNNEAAAAC/music-beat.gif")
        await ctx.send(embed=embed)

    @command(help="Change bot's prefix")
    async def setprefix(self, ctx: MyContext, new_prefix: str):
        if len(new_prefix) > 4:
            await ctx.reply("🚫 Please keep the length of prefix 4 or less characters")
            return
        else:
            await self.bot.db.execute(
                """INSERT INTO guilds (id, prefix) 
                VALUES ($1, $2) 
                ON CONFLICT (ID) DO UPDATE 
                    SET prefix = $2""",
                new_prefix,
                ctx.guild.id,  # type: ignore
            )
            await ctx.send("Prefix Updated!")
            self.bot.prefix[ctx.guild.id] = new_prefix  # type: ignore

    @setprefix.error  # type: ignore
    async def setprefix_error(self, ctx: MyContext, error: Exception):
        if isinstance(error, MissingPermissions):
            await ctx.send(
                "🚫 You dont have permission to change prefix -`Manage server`"
            )


def setup(bot: MyBot):
    bot.add_cog(Misc(bot))
