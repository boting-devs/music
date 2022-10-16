from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from io import BytesIO
from logging import getLogger
from random import sample, shuffle
from time import gmtime, strftime
from typing import TYPE_CHECKING

from botbase import MyContext
from cycler import cycler
from matplotlib import rc_context
from matplotlib.pyplot import close, savefig, subplots
from nextcord import ButtonStyle, Embed, File, Interaction, SelectOption
from nextcord.ext.menus import ButtonMenuPages, ListPageSource
from nextcord.ui import Button, Select, View, button, select
from pomice import Playlist, Track

from .playing_embed import playing_embed
from .types import MyInter

if TYPE_CHECKING:
    from nextcord import (
        Emoji,
        InteractionMessage,
        Message,
        PartialEmoji,
        PartialInteractionMessage,
    )

    from .types import Notification
    from .types import Playlist as SpotifyPlaylist


log = getLogger(__name__)


class LinkButtonView(View):
    def __init__(
        self, name: str, url: str, emoji: str | PartialEmoji | Emoji | None = None
    ):
        super().__init__()
        if emoji is not None:
            self.add_item(Button(label=name, url=url, emoji=emoji))
        else:
            self.add_item(Button(label=name, url=url))


class TimeoutView(View):
    message: Message

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)


class MyView(TimeoutView):
    """A collection of on_timeout: disable buttons and interaction_check: author"""

    inter: MyInter

    async def interaction_check(self, interaction: Interaction) -> bool:
        # user is an owner, or was the user that started the interaction.
        if interaction.user and interaction.user.id in (
            list(interaction.client.owner_ids) + [interaction.user.id]
        ):
            return True

        # We know the interaction that started this, send the error with a command.
        if self.inter and self.inter.application_command is not None:
            cmd = self.inter.application_command.qualified_name
            if not isinstance(cmd, str):
                cmd = cmd.name

            await interaction.response.send_message(
                f"This menu is for {self.inter.user.mention}, "
                f"use `/{cmd}` to have a menu to yourself.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"This menu is for {self.inter.user.mention}.",
                ephemeral=True,
            )

        # Do not contine with the button press.
        return False


class PlaylistView(MyView):
    message: Message | InteractionMessage | PartialInteractionMessage
    uri: str | None

    def __init__(self, playlists: list[SpotifyPlaylist]) -> None:
        super().__init__()
        # Split the playlists into chunks of 5 for the select menus.
        chunks = [playlists[i : i + 25] for i in range(0, len(playlists), 25)]

        # Only care about the first 5 chunks, thats 125, do they really need more?
        for chunk in chunks[:5]:
            self.add_item(PlaylistSelect(chunk))

        self.uri = None


class PlaylistSelect(Select[PlaylistView]):
    def __init__(self, chunk: list[SpotifyPlaylist]) -> None:
        super().__init__(
            placeholder="Select a playlist",
            min_values=1,
            max_values=1,
            options=[
                # Now this is confusing as hell.
                # This truncates the description to 100 chars if its above, with ...
                SelectOption(
                    label=(p["name"] or "No name defined?"),
                    description=(
                        (
                            p["description"]
                            if len(p["description"]) < 100
                            else p["description"][:97] + "..."
                        )
                        if p["description"]
                        else None
                    ),
                    value=p["external_urls"]["spotify"] or p["url"],
                )
                for p in chunk
            ],
        )

    async def callback(self, interaction: Interaction) -> None:
        assert self.view is not None
        self.view.uri = self.values[0]

        for child in self.view.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        await interaction.response.edit_message(view=self.view)

        self.view.stop()


class PlayButton(View):
    def __init__(
        self,
        track: Track | Playlist | None,
    ):
        super().__init__(timeout=None)

        if isinstance(track, Track):
            self.track = track
        else:
            self.track = None

    async def interaction_check(self, inter: Interaction) -> bool:
        inter = MyInter(inter, inter.client)  # type: ignore
        if not inter.guild or not inter.guild.voice_client:
            await inter.send_embed(
                "Not in Voice", "The bot needs to be connected to a vc!", ephemeral=True
            )
            return False
        elif (
            # User is not even in voice
            not inter.user.voice
            # Somehow they have a voice state but no channel?
            or not inter.user.voice.channel
            or inter.user.voice.channel.id != inter.guild.voice_client.channel.id
        ):
            await inter.send_embed(
                "Not in Voice",
                "You need to be in the same vc as the bot!",
                ephemeral=True,
            )
            return False

        return True

    @button(
        emoji="\U000023ef\U0000fe0f", style=ButtonStyle.blurple, custom_id="view:pp"
    )
    async def playpause(self, _: Button, inter: Interaction):
        assert inter.guild is not None
        inter = MyInter(inter, inter.client)  # type: ignore

        if not inter.guild.voice_client.is_paused:
            await inter.guild.voice_client.set_pause(True)
            await inter.send_author_embed("Paused")
        else:
            await inter.guild.voice_client.set_pause(False)
            await inter.send_author_embed("Resumed")

    @button(emoji="\U000023ed", style=ButtonStyle.blurple, custom_id="view:next")
    async def skip(self, _: Button, inter: Interaction):
        inter = MyInter(inter, inter.client)  # type: ignore
        assert inter.guild is not None

        player = inter.guild.voice_client

        if not player.queue:
            return await inter.send_embed("Nothing in queue", ephemeral=True)

        toplay = player.queue.pop(0)
        await player.play(toplay)
        await playing_embed(toplay, skipped_by=inter.user.mention)

    @button(emoji="\U000023f9", style=ButtonStyle.blurple, custom_id="view:stop")
    async def stop(self, _: Button, inter: Interaction):
        assert inter.guild is not None
        inter = MyInter(inter, inter.client)  # type: ignore

        if not inter.guild.voice_client.is_playing:
            return await inter.send_embed("No song is playing", ephemeral=True)

        inter.guild.voice_client.queue = []
        await inter.guild.voice_client.stop()
        await inter.send_author_embed("Stopped")

    @button(
        emoji="\U0001f500", style=ButtonStyle.blurple, custom_id="view:shuffle", row=1
    )
    async def shuffle(self, _: Button, inter: Interaction):
        assert inter.guild is not None
        inter = MyInter(inter, inter.client)  # type: ignore

        shuffle(inter.guild.voice_client.queue)
        await inter.send_author_embed("Shuffled the queue")

    @button(
        emoji="\U0001f523", style=ButtonStyle.blurple, custom_id="view:queue", row=1
    )
    async def queue(self, _: Button, inter: Interaction):
        assert inter.guild is not None
        inter = MyInter(inter, inter.client)  # type: ignore
        current = inter.guild.voice_client.current
        queue = inter.guild.voice_client.queue
        if not queue:
            return await inter.send_embed("Nothing in queue")

        menu = QueueView(source=QueueSource(current, queue), inter=inter)
        await menu.start(interaction=inter, ephemeral=True)

    @button(emoji="\U0001f502", style=ButtonStyle.blurple, custom_id="view:loop", row=1)
    async def loop(self, _: Button, inter: Interaction):
        assert inter.guild is not None
        inter = MyInter(inter, inter.client)  # type: ignore

        if not inter.guild.voice_client.is_playing:
            return await inter.send_embed("No song is playing", ephemeral=True)
        current_song = inter.guild.voice_client.current
        inter.guild.voice_client.queue.insert(0, current_song)
        await inter.send_author_embed("looping song once \U0001f502")

    @button(emoji="\U0001f90d", style=ButtonStyle.blurple, custom_id="view:like")
    async def like(self, _: Button, inter: Interaction):
        assert inter.guild is not None
        inter = MyInter(inter, inter.client)  # type: ignore

        if self.track is not None:
            await inter.bot.db.execute(
                """INSERT INTO song_data
                (id,
                lavalink_id
                spotify,
                name,
                artist,
                length,
                thumbnail,
                uri)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT DO UPDATE
                SET likes = song_data.likes + 1;
                INSERT INTO users (id) VALUES $9 ON CONFLICT DO NOTHING;
                INSERT INTO playlists (owner) VALUES $9 ON CONFLICT DO NOTHING;
                INSERT INTO song_to_playlist (song, playlist)
                    VALUES ($1, (SELECT id FROM playlists WHERE owner = $9))
                    ON CONFLICT DO NOTHING;
                """,
                self.track.identifier,
                self.track.track_id,
                self.track.spotify,
                self.track.title,
                self.track.author,
                self.track.length / 1000 if self.track.length is not None else 0,
                self.track.thumbnail,
                self.track.uri,
                inter.user.id,
            )
            await inter.send(f"Saved {self.track.title} to your liked songs!")
        else:
            await inter.send(
                "Could not save track, it is either a playlist, "
                "or Vibr restarted since it was played."
            )


class MyMenu(ButtonMenuPages):
    inter: MyInter


class QueueSource(ListPageSource):
    def __init__(self, now: Track, queue: list[Track]):
        super().__init__(entries=queue, per_page=10)
        self.queue = queue
        self.now = now
        self.title = f"Queue of {len(queue)} songs"

    def format_page(self, menu: MyMenu, tracks: list[Track]) -> Embed:
        add = self.queue.index(tracks[0]) + 1
        desc = "\n".join(
            # 1. title by author [length]
            f"**{i + add}.** [{t.title}]({t.uri}) by "
            f"{t.author} [{strftime('%H:%M:%S', gmtime((t.length or 0) / 1000))}]"
            for i, t in enumerate(tracks)
        )
        # This is the first page, share the now playing and next song.
        if tracks[0].track_id == self.queue[0].track_id:
            c = self.now
            desc = (
                f"\U0001f3b6 Now Playing:\n[{c.title}]({c.uri}) by {c.author}\n\n"
                f"\U0001f3b6 Up Next:\n" + desc
            )
        embed = Embed(
            description=desc,
            color=menu.ctx.bot.color if menu.ctx else menu.interaction.client.color,  # type: ignore
        )

        maximum = self.get_max_pages()
        # if maximum > 1:
        c = sum((t.length / 1000 if t.length else 0) for t in self.queue)
        a = strftime("%H:%M:%S", gmtime(round(c)))
        embed.set_footer(
            text=f"Page {menu.current_page + 1}/{maximum} "
            f"({len(self.queue)} tracks - total {a})"
        )

        embed.set_author(name=self.title)

        return embed


class QueueView(MyView, ButtonMenuPages):
    def __init__(self, source: ListPageSource, inter: MyInter) -> None:
        super().__init__(source=source, style=ButtonStyle.blurple)
        self.inter = inter

    @button(
        emoji="\U0001f500", style=ButtonStyle.blurple, row=1, custom_id="view:shuffle"
    )
    async def shuffle(self, _: Button, inter: Interaction):
        inter = MyInter(inter, inter.client)  # type: ignore
        if not inter.guild or not inter.guild.voice_client:
            await inter.send_embed(
                "Not in Voice", "The bot needs to be connected to a vc!", ephemeral=True
            )
            return
        elif (
            not inter.user
            or not inter.user.voice
            or not inter.user.voice.channel
            or inter.user.voice.channel.id != inter.guild.voice_client.channel.id
        ):
            await inter.send_embed(
                "Not in Voice",
                "You need to be in the same vc as the bot!",
                ephemeral=True,
            )
            return

        inter = MyInter(inter, inter.client)  # type: ignore

        shuffle(inter.guild.voice_client.queue)
        await inter.send_author_embed("Shuffled the queue")
        player = inter.guild.voice_client
        await self.change_source(QueueSource(player.current, player.queue))


class NotificationSource(ListPageSource):
    def __init__(self, notifications: list[Notification]):
        super().__init__(entries=notifications, per_page=1)
        self.title = f"Bot notifications (total: {len(notifications)})"

    def format_page(self, menu: MyMenu, notification: Notification) -> Embed:
        embed = Embed(
            description=notification.format(),
            color=menu.ctx.bot.color if menu.ctx else menu.interaction.client.color,  # type: ignore
        )

        embed.set_author(name=self.title)
        embed.set_footer(text=notification.time.strftime("%y-%m-%d"))

        return embed


class NotificationView(MyView, ButtonMenuPages):
    def __init__(self, source: ListPageSource, inter: MyInter) -> None:
        super().__init__(source=source, style=ButtonStyle.blurple)
        self.inter = inter


class StatsTime(Enum):
    """The time of stats to show."""

    ALL = str(timedelta(days=10**4).total_seconds())
    DAY = str(timedelta(days=1).total_seconds())
    WEEK = str(timedelta(days=7).total_seconds())
    MONTH = str(timedelta(days=30).total_seconds())


class StatsType(Enum):
    """The type of stats to show."""

    GUILDS = "guilds"
    COMMANDS = "commands"
    SONGS = "total_songs"
    PLAYERS = "active_players, total_players, listeners"
    LOAD = "lavalink_load, system_load"
    MEMORY = "memory_used, memory_allocated, memory_percentage"


TYPE_TO_TITLE: dict[StatsType, str] = {
    StatsType.GUILDS: "Guild Count",
    StatsType.COMMANDS: "Commands Used",
    StatsType.SONGS: "Songs Played",
    StatsType.PLAYERS: "Players/Listeners",
    StatsType.LOAD: "CPU Load",
    StatsType.MEMORY: "Memory Usage (MiB/%)",
}


class StatsView(TimeoutView):
    def __init__(self, ctx: MyContext) -> None:
        super().__init__()
        self.ctx = ctx

        self.timeframe = StatsTime.ALL
        self.type = StatsType.GUILDS

    @select(
        placeholder="Select a timeframe.",
        options=[
            SelectOption(label=name.title(), value=enum.value)
            for name, enum in StatsTime.__members__.items()
        ],
        min_values=1,
        max_values=1,
    )
    async def timeframe_select(self, select: Select, inter: Interaction):
        await inter.response.defer()
        await self.update_stats_time(select.values[0])

    @select(
        placeholder="Select a type.",
        options=[
            SelectOption(label=name.title(), value=enum.value)
            for name, enum in StatsType.__members__.items()
        ],
        min_values=1,
        max_values=1,
    )
    async def type_select(self, select: Select, inter: Interaction):
        await inter.response.defer()
        await self.update_stats_type(select.values[0])

    async def update_stats_type(self, value: str):
        self.type = StatsType(value)
        await self.update()

    async def update_stats_time(self, value: str):
        self.timeframe = StatsTime(value)
        await self.update()

    async def update(self):
        embed, file = await self.get_graph()
        await self.message.edit(embed=embed, file=file)

    async def get_graph(self) -> tuple[Embed, File]:
        data = await self.ctx.bot.db.fetch(
            # Yes an f-string in SQL, to actually interpolate as the column.
            # The values here is only controlled by us so it is safe.
            f"""SELECT time, {self.type.value} FROM hourly_stats
            WHERE time > now() - $1::interval""",
            timedelta(seconds=float(self.timeframe.value)),
        )

        embed = Embed(title="Stats", color=self.ctx.bot.color)

        colours = [f"#{hex(c)[2:]}" for c in self.ctx.bot.colors]
        with rc_context(
            {
                "axes.prop_cycle": cycler(color=sample(colours, len(colours))),
                "figure.constrained_layout.use": True,
                "axes.facecolor": "#272934",
                "axes.edgecolor": "white",
                "figure.facecolor": "black",
                "axes.labelcolor": "white",
                "xtick.color": "white",
                "ytick.color": "white",
                "text.color": "white",
                "legend.framealpha": 1,
            }
        ):
            figure, axes = subplots()
            axes.set_title(
                f"{TYPE_TO_TITLE[self.type]} ({self.timeframe.name.title()})"
            )

            times = []

            # No clue why postgres decides its in one day but 00:00 is the next?
            for row in data:
                time: datetime = row["time"]
                if time.hour == 0:
                    times.append(time.replace(day=time.day + 1))
                else:
                    times.append(time)

            handles = [
                axes.plot(
                    times,
                    [row[t] for row in data],
                    label=t.replace("_", " ").title(),
                )[0]
                for t in self.type.value.split(", ")
            ]
            axes.legend(handles=handles)

            b = BytesIO()

            try:
                savefig(b, format="png", bbox_inches="tight")
            finally:
                close()

        b.seek(0)
        file = File(
            b,
            filename="stats.png",
            description=(
                f"Stats for {self.type.value} "
                f"over the last {self.timeframe.name.lower()}."
            ),
        )
        embed.set_image("attachment://stats.png")

        return embed, file
