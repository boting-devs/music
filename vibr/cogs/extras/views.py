from __future__ import annotations

from random import shuffle
from time import gmtime, strftime
from typing import TYPE_CHECKING

from nextcord import ButtonStyle, Embed, Interaction, SelectOption
from nextcord.ext.menus import ButtonMenuPages, ListPageSource
from nextcord.ui import Button, Select, View, button

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
    from pomice import Track

    from .types import Notification, Playlist


class LinkButtonView(View):
    def __init__(
        self, name: str, url: str, emoji: str | PartialEmoji | Emoji | None = None
    ):
        super().__init__()
        if emoji is not None:
            self.add_item(Button(label=name, url=url, emoji=emoji))
        else:
            self.add_item(Button(label=name, url=url))


class PlaylistView(View):
    message: Message | InteractionMessage | PartialInteractionMessage
    uri: str | None

    def __init__(self, playlists: list[Playlist]) -> None:
        super().__init__()
        chunks = [playlists[i : i + 10] for i in range(0, len(playlists), 25)]

        for chunk in chunks:
            self.add_item(PlaylistSelect(chunk))

        self.uri = None

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        await self.message.edit(view=self)


class PlaylistSelect(Select[PlaylistView]):
    def __init__(self, chunk: list[Playlist]) -> None:
        super().__init__(
            placeholder="Select a playlist",
            min_values=1,
            max_values=1,
            options=[
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
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, inter: Interaction) -> bool:
        inter = MyInter(inter, inter.client)  # type: ignore
        if not inter.guild or not inter.guild.voice_client:
            await inter.send_embed(
                "Not in Voice", "The bot needs to be connected to a vc!", ephemeral=True
            )
            return False
        elif (
            not inter.user.voice
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
        await playing_embed(toplay, volume=player.volume, skipped_by=inter.user.mention)

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
            f"**{i + add}.** [{t.title}]({t.uri}) by "
            f"{t.author} [{strftime('%H:%M:%S', gmtime((t.length or 0) / 1000))}]"
            for i, t in enumerate(tracks)
        )
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


class MyView(View):
    """A collection of on_timeout: disable buttons and interaction_check: author"""

    inter: MyInter
    message: Message

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user and interaction.user.id in (
            list(self.interaction.client.owner_ids) + [self.interaction.user.id]  # type: ignore
        ):
            return True
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
        return False

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)


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
