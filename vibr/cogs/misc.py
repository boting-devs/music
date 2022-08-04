from __future__ import annotations

from typing import TYPE_CHECKING, Union

from nextcord.ext.commands import Cog, command
from nextcord import Embed, Message, slash_command

from .extras.types import MyContext, MyInter

if TYPE_CHECKING:
    from ..__main__ import Vibr


TEST = [802586580766162964, 939509053623795732]


class Misc(Cog, name="misc", description="Meta commands about the bot!"):
    def __init__(self, bot: Vibr):
        self.bot = bot

    @property
    def emoji(self) -> str:
        return "⚙️"

    @slash_command(name="ping", description="Pong!")
    async def ping_(self, inter: MyInter):
        return await self.ping(inter)  # type: ignore

    @command(help="Ping command")
    async def ping(self, ctx: Union[MyContext, MyInter]):
        await ctx.send(f"🏓 Pong! `{round(self.bot.latency * 1000)} ms`")

    @slash_command(name="invite", description="Invite me!")
    async def invite_(self, inter: MyInter):
        return await self.invite(inter)  # type: ignore

    @command(help="invite me!")
    async def invite(self, ctx: Union[MyContext, MyInter]):
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

    @slash_command(name="support", description="Get some help")
    async def support_(self, inter: MyInter):
        return await self.support(inter)  # type: ignore

    @command(help="Vibr support server link")
    async def support(self, ctx: Union[MyContext, MyInter]):
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
                    f"To view all the commands use `{prefix}help`**",
                    color=self.bot.color,
                )
                await message.channel.send(embed=embed)

    @slash_command(name="vote", description="Vote for meee")
    async def vote_(self, inter: MyInter):
        return await self.vote(inter)  # type: ignore

    @command(help="Vote for vibr")
    async def vote(self, ctx: Union[MyContext, MyInter]):
        embed = Embed(title="**Vote for Vibr**", color=self.bot.color)
        embed.add_field(
            name="Like our bot? Vote for us",
            value="[click here](https://top.gg/bot/882491278581977179)",
        )
        embed.set_image(
            url="https://d30i16bbj53pdg.cloudfront.net/wp-content/uploads/2018/10/vote-for-blog.jpg"
        )
        await ctx.send(embed=embed)

    @command(hidden = True)
    async def notif_create(self,ctx:Union[MyContext,MyInter],notification):
        await self.bot.db.execute("INSERT INTO notifications(notification) VALUES($1)",notification)
        await ctx.send("Saved in db")

    @command(hidden=True)
    async def notifications(self,ctx:Union[MyContext,MyInter]):
        outp=[]
        notifs = await self.bot.db.fetch("SELECT notification,datetime FROM notifications ORDER BY id DESC")
        outp.append(notifs)
        embed = Embed(title="Vibr's Notifications",description="**__List of vibr's important announcements/notifications__**",color=self.bot.color)
        stop = 10
        for (index,value) in enumerate(notifs[:stop],start=1):
            embed.add_field(name=f'{index}) **{value["notification"]}**',value=f'{value["datetime"]}',inline=False)
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)


def setup(bot: Vibr):
    bot.add_cog(Misc(bot))
