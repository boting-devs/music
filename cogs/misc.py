from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord import Embed, Message
from nextcord.ext.commands import Cog, command, MissingPermissions

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

    @Cog.listener()
    async def on_message(self, message: Message):
        assert self.bot.user is not None
        if self.bot.user.mentioned_in(message):
            if message.content in ("<@882491278581977179>", "<@!882491278581977179>"):
                prefix = await self.bot.get_prefix(message)
                prefix = prefix[-1]
                embed = Embed(
                    title="Hi my name is Vibr",
                    description=f"**My prefix is `{prefix}`\n"
                                f"To view all the commands use `{prefix.strip()} help`**",
                    color=self.bot.color,
                )
                await message.channel.send(embed=embed)

    @command(help="Vote for vibr")
    async def vote(self,ctx:MyContext):
        embed = Embed(title="**Vote for Vibr**",color=self.bot.color)
        embed.add_field(name="Like our bot? Vote for us",value="[click here](https://top.gg/bot/882491278581977179)")
        embed.set_image(url="https://d30i16bbj53pdg.cloudfront.net/wp-content/uploads/2018/10/vote-for-blog.jpg")
        await ctx.send(embed=embed) 


def setup(bot: MyBot):
    bot.add_cog(Misc(bot))
