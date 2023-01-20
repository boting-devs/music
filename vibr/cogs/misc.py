from __future__ import annotations

from asyncio import sleep
from datetime import timedelta
from logging import getLogger
from os import getenv
from typing import TYPE_CHECKING

from humanfriendly import parse_timespan
from nextcord import Embed, Message, Permissions, TextInputStyle, slash_command
from nextcord.ext.application_checks import is_owner
from nextcord.ext.commands import Cog, Converter
from nextcord.ext.tasks import loop
from nextcord.ui import Modal, TextInput
from nextcord.utils import utcnow

from pomice import NoNodesAvailable

from .extras.types import MyInter, Notification
from .extras.views import NotificationSource, NotificationView , StatsView

if TYPE_CHECKING:

    from ..__main__ import Vibr


log = getLogger(__name__)
TEST_IDS = [939509053623795732]

STATS: str="""
Guilds: `{guilds:,}`
Commands used: `{commands:,}`
Songs Played:`{songs:,}`
Total Players: `{total_players:,}`
Users Listening: `{listeners:,}`
""".strip()


class NotificationCreate(Modal):
    def __init__(self):
        super().__init__(title="Create a Notification")

        self._title = TextInput(
            label="Enter a title for the notification.", max_length=256, required=True
        )
        self.time = TextInput(
            label="Enter an expiry time for the notification",
            required=True,
            default_value="7d",
        )
        self.description = TextInput(
            label="Enter a description for the notification",
            required=True,
            style=TextInputStyle.paragraph,
        )

        self.add_item(self._title)
        self.add_item(self.time)
        self.add_item(self.description)

    async def callback(self, inter: MyInter):
        title = self._title.value
        notification = self.description.value

        try:
            if self.time.value is None:
                raise ValueError

            expiry = timedelta(seconds=parse_timespan(self.time.value))
        except ValueError:
            await inter.response.send_message(
                "Invalid time, please try again.", ephemeral=True
            )
            return

        await inter.client.db.execute(
            """INSERT INTO notifications(title, notification, expiry)
            VALUES ($1, $2, $3)""",
            title,
            notification,
            utcnow() + expiry,
        )
        await inter.send("Saved in db")

        await inter.client.db.execute("UPDATE users SET notified=false")
        inter.client.notified_users.clear()
        await inter.send("Set all users to un-notified")
        log.info("Distributing notification %s", title)


class Misc(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot

        self.topgg.start()

    def cog_unload(self):
        self.topgg.stop()

    @loop(minutes=30)
    async def topgg(self):
        if getenv("topgg_token") is None:
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

    @slash_command()
    async def ping(self, inter: MyInter):
        """Pong!"""

        await inter.send(f"🏓 Pong! `{round(self.bot.latency * 1000)} ms`")

    @slash_command()
    async def invite(self, inter: MyInter):
        """Invite me!"""

        servers = self.bot.guilds
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
        await inter.send(embed=embed)

    @slash_command()
    async def support(self, inter: MyInter):
        """My support server's link."""

        embed = Embed(title="**Support Link**", color=self.bot.color)
        embed.add_field(
            name="**Facing any problem? Join the support server**",
            value="**[click here](https://discord.gg/v3UvgPXwHq)**",
        )
        embed.set_image(url="https://c.tenor.com/lhlDEs5fNNEAAAAC/music-beat.gif")
        await inter.send(embed=embed)

    @Cog.listener()
    async def on_message(self, message: Message):
        assert self.bot.user is not None
        if self.bot.user.mentioned_in(message):
            if message.content in ("<@882491278581977179>", "<@!882491278581977179>"):
                prefix = await self.bot.get_prefix(message)
                prefix = prefix[-1]
                embed = Embed(
                    title="Hi my name is Vibr",
                    description="**I now use slash commands**\n"
                    "if these do not show up, make sure you have the `Use Application Commands`"
                    "permission, if so then please re-invite (**no need to kick**) with "
                    "[this link](https://discord.com/api/oauth2/authorize?client_id=882491278581977179&permissions=3427392&scope=bot%20applications.commands)",
                    color=self.bot.color,
                )

                perms = message.channel.permissions_for(message.guild.me)  # type: ignore
                if perms.send_messages and perms.view_channel:
                    await message.channel.send(embed=embed)

    @slash_command()
    async def vote(self, inter: MyInter):
        """Vote for me!"""

        embed = Embed(title="**Vote for Vibr**", color=self.bot.color)
        embed.add_field(
            name="Like our bot? Vote for us",
            value="[click here](https://top.gg/bot/882491278581977179)",
        )
        embed.set_image(
            url="https://d30i16bbj53pdg.cloudfront.net/wp-content/uploads/2018/10/vote-for-blog.jpg"
        )
        await inter.send(embed=embed)

    @slash_command(
        name="create-notification",
        default_member_permissions=Permissions(8),
        guild_ids=TEST_IDS,
    )
    @is_owner()
    async def create_notification(self, inter: MyInter):
        """Create a notification."""

        await inter.response.send_modal(NotificationCreate())

    @slash_command()
    async def notifications(self, _: MyInter):
        ...

    @notifications.subcommand(name="toggle")
    async def notifications_toggle(self, inter: MyInter):
        """Toggle notification messages for you."""

        enabled = await self.bot.db.fetchval(
            "SELECT notifications FROM users WHERE id=$1", inter.user.id
        )

        if enabled is None:
            enabled = True

        new = not enabled

        await self.bot.db.execute(
            """INSERT INTO users (id, notifications)
            VALUES ($1, $2)
            ON CONFLICT (id) DO UPDATE
                SET notifications=$2""",
            inter.user.id,
            new,
        )

        await inter.send(
            f"Notifications are now {'enabled' if new else 'disabled'} for you.",
            ephemeral=True,
        )

    @notifications.subcommand(name="list")
    async def notifications_list(self, inter: MyInter):
        """Recent announcements/notifications."""

        notifs = await self.bot.db.fetch("SELECT * FROM notifications ORDER BY id DESC")
        if not notifs:
            return await inter.send("No notifications are available")

        menu = NotificationView(
            source=NotificationSource(list(map(Notification, notifs))), inter=inter
        )
        await menu.start(interaction=inter, ephemeral=True)

    @slash_command()
    async def donate(self, inter: MyInter):
        """Donate to vibr"""
        embed = Embed(title="**Support Me :)**", color=self.bot.color)
        embed.add_field(
            name="**Enjoy the bot? Help us keep it the way it is**",
            value="**[click here](https://paypal.me/botingdevs)**",
        )
        embed.set_image(
            url="https://lacountylibrary.org/wp-content/uploads/2018/10/eNews-ThankYouLarge-1170x658.jpg"
        )
        await inter.send(embed=embed)

    @slash_command()
    async def botstats(self , inter:MyInter):
        """Stats about Vibr Bot"""
        stats = None
        for tries in range(5):
            try:
                node = self.bot.pool.get_node()
            except NoNodesAvailable:
                await sleep(2.5 * tries)
            else:
                stats = node.stats
        
        guilds = len(self.bot.guilds)
        commands = await self.bot.db.fetchval("SELECT SUM(amount) FROM commands")
        songs = await self.bot.db.fetchval("SELECT SUM(amount) FROM songs")

        channels = [v.channel.id for v in self.bot.voice_clients]
        
        embed = Embed(title="**Vibr Stats**",
        description=STATS.format(
            guilds = guilds,
            commands = commands,
            songs = songs,
            total_players = stats.players_total or 0,
            listeners=sum(
                    len(listeners)
                    for channel, listeners in self.bot.listeners.items()
                    if channel in channels
                ),
            ),
            color= self.bot.color,
            
        )
        view = StatsView(inter,public=True)
        await inter.send(embed=embed)
        m = await inter.send(view=view)
        view.message = m
        await view.update()
        

        


def setup(bot: Vibr):
    bot.add_cog(Misc(bot))
