from __future__ import annotations

from asyncio import sleep
from os import getenv

from botbase import CogBase
from nextcord import slash_command
from nextcord.ext.tasks import loop
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter


class Misc(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        self.bot = bot
        self.topgg.start()

    def cog_unload(self) -> None:
        self.topgg.stop()

    @loop(minutes=30)
    async def topgg(self) -> None:
        if getenv("TOPGG_TOKEN") is None:  # add top.gg token
            return

        headers = {"Authorization": getenv("TOPGG_TOKEN")}
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
    async def topgg_before_loop(self) -> None:
        await self.bot.wait_until_ready()
        await sleep(20)

    @slash_command(dm_permission=False)
    async def ping(self, inter: Inter) -> None:
        """Pong!"""

        await inter.send(f"🏓 Pong! `{round(self.bot.latency * 1000)} ms`")

    @slash_command()
    async def invite(self, inter: Inter) -> None:
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
    async def support(self, inter: Inter) -> None:
        """My support server's link."""

        embed = Embed(title="**Support Link**")
        embed.add_field(
            name="**Facing any problem? Join the support server**",
            value="**[click here](https://discord.gg/v3UvgPXwHq)**",
        )
        embed.set_image(url="https://c.tenor.com/lhlDEs5fNNEAAAAC/music-beat.gif")
        await inter.send(embed=embed)

    @slash_command()
    async def vote(self, inter: Inter) -> None:
        """Vote for me!"""

        embed = Embed(title="**Vote for Vibr**", timestamp=utcnow())
        embed.add_field(
            name="Like our bot? Vote for us",
            value="[click here](https://top.gg/bot/882491278581977179)",
        )
        embed.set_image(
            url="https://d30i16bbj53pdg.cloudfront.net/wp-content/uploads/2018/10/vote-for-blog.jpg"
        )
        await inter.send(embed=embed)

    @slash_command()
    async def donate(self, inter: Inter) -> None:
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


def setup(bot: Vibr) -> None:
    bot.add_cog(Misc(bot))
