from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.embed import Embed
from vibr.inter import Inter


class Misc(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        self.bot = bot

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

        embed = Embed(title="**Vote for Vibr**")
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
            name="**Enjoy the bot? Help us keep it running!**",
            value="**[click here](https://donate.stripe.com/eVa9DSdGs0Qed8s7ss)**",
        )
        embed.set_image(
            url="https://i.postimg.cc/zG6kL55F/e-News-Thank-You-Large-1170x658.jpg"
        )
        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Misc(bot))
