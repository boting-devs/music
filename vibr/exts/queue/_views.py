from __future__ import annotations

from time import gmtime, strftime
from typing import TYPE_CHECKING, cast

from nextcord import ButtonStyle, Embed
from nextcord.abc import Snowflake
from nextcord.ext.menus import ButtonMenuPages, ListPageSource
from nextcord.ui import Button, Select

from vibr.patches.nextcord.ui import button

if TYPE_CHECKING:
    from mafic import Track
    from nextcord import PartialInteractionMessage

    from vibr.inter import Inter
    from vibr.player import Queue


class QueueMenu(ButtonMenuPages):
    message: PartialInteractionMessage
    interaction: Inter

    def __init__(self, source: QueueSource, inter: Inter) -> None:
        super().__init__(source=source, style=ButtonStyle.blurple)
        self.interaction = inter

    async def on_timeout(self) -> None:
        self.stop()

        for child in self.children:
            if isinstance(child, Button | Select):
                child.disabled = True

        await self.message.edit(view=self)

    async def interaction_check(self, inter: Inter) -> bool:
        # user is an owner, or was the user that started the interaction.
        if inter.user and inter.user.id in ([*inter.client.owner_ids, inter.user.id]):
            return True

        cmd = inter.client.get_command_mention("queue")
        await inter.response.send_message(
            f"This menu is for {self.interaction.user.mention}, "
            f"use `{cmd}` to have a menu to yourself.",
            ephemeral=True,
        )

        # Do not contine with the button press.
        return False

    @button(emoji="\U0001f500", style=ButtonStyle.grey, row=1)
    async def shuffle(self, _: Button, inter: Inter) -> None:
        if not inter.guild or not inter.guild.voice_client:
            await inter.send_embed(
                "Not in Voice", "The bot needs to be connected to a vc!", ephemeral=True
            )
            return

        if (
            not inter.user
            or not inter.user.voice
            or not inter.user.voice.channel
            or inter.user.voice.channel.id
            != cast(Snowflake, inter.guild.voice_client.channel).id
        ):
            await inter.send_embed(
                "Not in Voice",
                "You need to be in the same vc as the bot!",
                ephemeral=True,
            )
            return

        player = inter.guild.voice_client

        if not player.current:
            await inter.send_embed(
                "No Song", "There is no song playing!", ephemeral=True
            )
            return

        player.queue.shuffle()
        await inter.send_author_embed("Shuffled the queue")
        await self.change_source(QueueSource(player.current, player.queue))


class QueueSource(ListPageSource):
    def __init__(self, now: Track, queue: Queue) -> None:
        tracks = queue.tracks
        super().__init__(entries=tracks, per_page=10)
        self.queue = tracks
        self.now = now
        self.title = f"Queue of {len(queue)} songs"

    def format_page(self, menu: QueueMenu, tracks: list[Track]) -> Embed:
        add = self.queue.index(tracks[0]) + 1

        desc = "\n".join(
            # 1. title by author [length]
            f"**{i + add}.** [{t.title}]({t.uri}) by "
            f"{t.author} [{strftime('%H:%M:%S', gmtime((t.length or 0) / 1000))}]"
            for i, t in enumerate(tracks)
        )
        # This is the first page, share the now playing and next song.
        if tracks[0] == self.queue[0]:
            c = self.now
            desc = (
                f"\U0001f3b6 Now Playing:\n[{c.title}]({c.uri}) by {c.author}\n\n"
                f"\U0001f3b6 Up Next:\n" + desc
            )

        embed = Embed(
            description=desc,
            color=menu.interaction.client.colour,
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
