from __future__ import annotations

from typing import TYPE_CHECKING
from os import getenv
from asyncio import sleep

from botbase import CogBase, MyInter
from nextcord import slash_command,Message
from nextcord.utils import utcnow
from nextcord.ext.commands import Cog
from nextcord.ext.tasks import loop
from vibr.bot import Vibr

from vibr.embed import Embed


class Misc(CogBase[Vibr]):
    def __init__(self,bot:Vibr):
        self.bot = bot
        self.topgg.start()

    def cog_unload(self):
        self.topgg.stop()
    
    @loop(minutes=30)
    async def topgg(self):
        if getenv("topgg_token") is None:              #add top.gg token
            return

        headers = {"Authorization": getenv("topgg_token")}
        data = {
            "server_count": len(self.bot.guilds),
            "shard_count": self.bot.shard_count or 1,
        }
        assert self.bot.user is not None
        await self.bot.session.post(
            f"https://top.gg/api/bots/{self.bot.user.id}/stats",
            headers=headers,
            data=data,
        )

    @topgg.before_loop
    async def topgg_before_loop(self):
        await self.bot.wait_until_ready()
        await sleep(20)

    @slash_command(dm_permission=False)
    async def ping(self,inter:MyInter):
        """Pong!"""

        await inter.send(f"🏓 Pong! `{round(self.bot.latency * 1000)} ms`")
    
    @slash_command()
    async def invite(self, inter: MyInter):
        """Invite me!"""

        servers = self.bot.guilds
        embed = Embed(title="**Invite Link**")
        embed.add_field(
            name=f"**The bot is currently in {len(servers)} servers**",
            value="**[invite me](https://discord.com/api/oauth2/authorize?"
            "client_id=882491278581977179&permissions=274919115840&scope=bot"
            "%20applications.commands)**",
        )
        embed.set_image(
            url="https://learnenglishfunway.com/wp-content/uploads/2020/12/Music-2.jpg"
        )
        await inter.send(embed=embed)


    @slash_command()
    async def support(self, inter: MyInter):
        """My support server's link."""

        embed = Embed(title="**Support Link**")
        embed.add_field(
            name="**Facing any problem? Join the support server**",
            value="**[click here](https://discord.gg/v3UvgPXwHq)**",
        )
        embed.set_image(url="https://c.tenor.com/lhlDEs5fNNEAAAAC/music-beat.gif")
        await inter.send(embed=embed)

    @slash_command()
    async def vote(self, inter: MyInter):
        """Vote for me!"""

        embed = Embed(title="**Vote for Vibr**",timestamp=utcnow())
        embed.add_field(
            name="Like our bot? Vote for us",
            value="[click here](https://top.gg/bot/882491278581977179)",
        )
        embed.set_image(
            url="https://d30i16bbj53pdg.cloudfront.net/wp-content/uploads/2018/10/vote-for-blog.jpg"
        )
        await inter.send(embed=embed)

    @slash_command()
    async def donate(self, inter: MyInter):
        """Donate to vibr"""
        embed = Embed(title="**Support Me :)**")
        embed.add_field(
            name="**Enjoy the bot? Help us keep it the way it is**",
            value="**[click here](https://donate.stripe.com/eVa9DSdGs0Qed8s7ss)**",
        )
        embed.set_image(
            url="https://i.postimg.cc/zG6kL55F/e-News-Thank-You-Large-1170x658.jpg"
        )
        await inter.send(embed=embed)

def setup(bot:Vibr) ->None:
    bot.add_cog(Misc(bot))