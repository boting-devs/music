from __future__ import annotations

from typing import TYPE_CHECKING, cast

from mafic import Playlist, Track
from nextcord import ButtonStyle
from nextcord.abc import Snowflake
from nextcord.ui import Button, Select, View

from vibr.checks import voted_predicate
from vibr.database import add_to_liked
from vibr.embed import Embed, ErrorEmbed
from vibr.errors import NotVoted
from vibr.exts.playing._errors import LyricsNotFound
from vibr.inter import Inter
from vibr.patches.nextcord.ui import button

from .exts.queue._views import QueueMenu, QueueSource

if TYPE_CHECKING:
    from nextcord import Message, PartialInteractionMessage


class TimeoutView(View):
    message: Message | PartialInteractionMessage | None = None

    async def on_timeout(self) -> None:
        self.stop()

        for child in self.children:
            if isinstance(child, Button | Select):
                child.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)


MULTI_LOOP = "<:loopall:1044708055234904094>"
SINGLE_LOOP = "<:loop:1044708068639903907>"


class PlayButtons(TimeoutView):
    def __init__(
        self,
        track: Track | Playlist | None,
        *,
        loop: bool = False,
    ) -> None:
        super().__init__(timeout=60 * 5)

        if isinstance(track, Track):
            self.track = track
        else:
            self.track = None

        if loop:
            self.loop.emoji = MULTI_LOOP
            self.loop.style = ButtonStyle.grey

    async def interaction_check(self, inter: Inter) -> bool:
        if not inter.guild or not inter.guild.voice_client:
            embed = Embed(
                title="Not in Voice",
                description="The bot needs to be connected to a vc!",
            )
            await inter.send(embed=embed, ephemeral=True)
            return False

        if (
            # User is not even in voice
            not inter.user.voice
            # Somehow they have a voice state but no channel?
            or not inter.user.voice.channel
            or inter.user.voice.channel.id
            != cast(Snowflake, inter.guild.voice_client.channel).id
        ):
            embed = Embed(
                title="Not in Voice",
                description="You need to be in the same vc as the bot!",
            )
            await inter.send(embed=embed, ephemeral=True)
            return False

        return True

    @button(emoji="<:playpause:1044619888146255975>", style=ButtonStyle.blurple)
    async def playpause(self, _: Button, inter: Inter) -> None:
        player = inter.guild.voice_client

        if player.current is None:
            embed1 = ErrorEmbed(
                title="No song Playing",
                description="Use /play a song to use the command",
            )
            await inter.send(embed=embed1, ephemeral=True)
            return

        if player.paused is False:
            await player.pause(pause=True)
            embed = Embed(title="Paused")
        else:
            await player.resume()
            await player.pause(pause=False)
            embed = Embed(title="Resumed")

        await inter.send(embed=embed)
        return

    @button(emoji="<:stop:1044661767504134164>", style=ButtonStyle.blurple)
    async def stop_(self, _: Button, inter: Inter) -> None:
        player = inter.guild.voice_client
        if player.current is None:
            embed1 = ErrorEmbed(
                title="No song Playing",
                description="Use /play a song to use the command",
            )
            await inter.send(embed=embed1, ephemeral=True)
            return

        player.queue.clear()
        await player.stop()

        embed = Embed(
            title="Stopped",
        )
        await inter.send(embed=embed)
        return

    @button(emoji="<:skip:1044620351390363739>", style=ButtonStyle.blurple)
    async def skip_(self, _: Button, inter: Inter) -> None:
        from vibr.track_embed import track_embed

        player = inter.guild.voice_client

        if not player.queue:
            embed = Embed(title="Queue is empty")
            await inter.send(embed=embed)
            return

        track, user = player.queue.skip(1)
        await player.play(track)
        embed, view = await track_embed(track, skipped=inter.user.id)
        m = await inter.response.send_message(embed=embed, view=view)
        view.message = m
        return

    @button(emoji="<:queue:1044702819992748138>", style=ButtonStyle.blurple, row=1)
    async def queue(self, _: Button, inter: Inter) -> None:
        current = inter.guild.voice_client.current
        queue = inter.guild.voice_client.queue

        if not queue and not current:
            embed = Embed(title="Queue is empty")
            await inter.send(embed=embed)
            return

        menu = QueueMenu(source=QueueSource([current, *queue]), inter=inter)
        await menu.start(interaction=inter)

    @button(emoji=MULTI_LOOP, style=ButtonStyle.blurple, custom_id="view:loop")
    async def loop(self, button: Button, inter: Inter) -> None:
        player = inter.guild.voice_client

        if button.style is ButtonStyle.blurple and str(button.emoji) == MULTI_LOOP:
            player.queue.loop_track(player.current, user=inter.user.id)
            button.emoji = SINGLE_LOOP
            embed = Embed(title="Looping Current Track Infinitely")

        elif button.style is ButtonStyle.blurple and str(button.emoji) == SINGLE_LOOP:
            player.queue.loop_track_once(player.current, user=inter.user.id)
            button.style = ButtonStyle.grey
            embed = Embed(title="Switching Loop Type to Once")
        else:
            player.queue.disable_loop()
            button.emoji = MULTI_LOOP
            button.style = ButtonStyle.blurple
            embed = Embed(title="Track Looping Disabled")

        await inter.edit(view=self)
        await inter.send(embed=embed)

    @button(emoji="<:vibrheart:1044662164587290664>", style=ButtonStyle.blurple, row=1)
    async def like(self, _: Button, inter: Inter) -> None:
        existed = await add_to_liked(user=inter.user, track=self.track)
        if existed:
            await inter.send(
                f"**{self.track.title}** is already in your liked playlist!"
            )

        else:
            await inter.send(f"**{self.track.title}** added to your liked playlist!")

    @button(emoji="<:lyrics:1114702495722262669>", style=ButtonStyle.blurple, row=1)
    async def lyrics(self, _: Button, inter: Inter) -> None:
        try:
            await voted_predicate(inter)
        except NotVoted as e:
            await inter.send(embed=e.embed, view=e.embed.view)
            return

        try:
            await inter.client.lyrics(inter, self.track.title)
        except LyricsNotFound as e:
            await inter.send(embed=e.embed, view=e.embed.view)

    @button(emoji="<:remove:1114702473249161226>", style=ButtonStyle.blurple, row=1)
    async def remove(self, _: Button, inter: Inter) -> None:
        player = inter.guild.voice_client
        try:
            index = player.queue.index(self.track)
            player.queue.pop(index)
        except Exception:
            await inter.send("This song is not in the queue", ephemeral=True)
            return
        embed = Embed(title=f"Removed **{self.track.title}** from the queue")
        await inter.send(embed=embed)
        return
