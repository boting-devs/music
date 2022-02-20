from __future__ import annotations

from asyncio import sleep
from inspect import signature
from logging import getLogger
from random import shuffle
from time import gmtime, strftime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from nextcord import ButtonStyle, ClientUser, Embed, Interaction, Member, User
from nextcord.ext.commands import (
    BotMissingPermissions,
    Cog,
    Context,
    MissingRequiredArgument,
    NoPrivateMessage,
    check,
    command,
)
from nextcord.ext.menus import ButtonMenuPages, ListPageSource
from nextcord.ui import Button, View, button, Select
from nextcord.utils import utcnow, MISSING
from pomice import Playlist

from .extras.errors import (
    NotConnected,
    NotInVoice,
    TooManyTracks,
    LyricsNotFound,
    NotInSameVoice,
)
from .extras.types import MyContext, MyInter, Player, SpotifyPlaylists

if TYPE_CHECKING:
    from nextcord import VoiceState
    from pomice import Track

    from ..mmain import MyBot


log = getLogger(__name__)

API_URL = "https://api.genius.com/search/"
TKN = "E4Eq5BhA2Xq6U99o1swO5IWcS7BBKyx1lCzyApT1wbyEqhItNaK5PpukKpUKrt3G"


def connected():
    async def extended_check(ctx: Context) -> bool:
        if ctx.voice_client is None:
            raise NotConnected()

        return True

    return check(extended_check)


async def playing_embed(
    track: Track | Playlist,
    queue: bool = False,
    length: bool = False,
    skipped_by: str | None = None,
    override_ctx: MyContext | None = None,
):
    view = PlayButton()
    if isinstance(track, Playlist):
        assert track.tracks[0].ctx is not None

        ctx: MyContext = track.tracks[0].ctx  # type: ignore

        title = track.name
        author = "Multiple Authors"
        time = strftime(
            "%H:%M:%S",
            gmtime(sum(t.length for t in track.tracks if t.length is not None) / 1000),
        )
    else:
        assert track.ctx is not None

        ctx: MyContext = track.ctx  # type: ignore
        title = track.title
        author = track.author
        if not track.length:
            time = "Unknown"
        else:
            time = strftime(
                "%H:%M:%S",
                gmtime(track.length / 1000),
            )

    if override_ctx:
        ctx = override_ctx

    embed = Embed(
        color=ctx.bot.color,
        timestamp=utcnow(),
    )

    if length:
        if isinstance(track, Playlist):
            tr = track.tracks[0]
        else:
            tr = track

        c = ctx.voice_client.position
        assert tr.length is not None
        t = tr.length
        current = strftime("%H:%M:%S", gmtime(c // 1000))
        total = strftime("%H:%M:%S", gmtime(t // 1000))
        pos = round(c / t * 12)
        line = (
            ("\U00002501" * (pos - 1 if pos > 0 else 0))
            + "\U000025cf"
            + ("\U00002501" * (12 - pos))
        )
        # if 2/12, then get 1 before, then dot then 12 - 2 to pad to 12
        timing = f"{current} {line} {total}"
        embed.description = ctx.author.mention + "\n" + timing
    else:
        embed.description = f"{time} - {ctx.author.mention}"

    if skipped_by:
        embed.description = embed.description + "\n skipped by " + skipped_by

    if author == None:
        embed.set_author(name=str(title), url=track.uri)

    else:
        embed.set_author(name=str(title) + " - " + str(author), url=track.uri)

    if track.thumbnail:
        embed.set_thumbnail(url=track.thumbnail)

    if queue:
        await ctx.send(embed=embed, content="Queued", view=view)
        return
    if length:
        channel = ctx.channel
        await channel.send(embed=embed, view=view)
    else:
        await ctx.send(embed=embed, view=view)

        if isinstance(track, Playlist):
            return

        await ctx.bot.db.execute(
            """INSERT INTO songs (id, spotify, member) 
            VALUES ($1, $2, $3) 
            ON CONFLICT (id, spotify, member)
            DO UPDATE SET
                amount = songs.amount + 1""",
            track.identifier,
            track.spotify,
            ctx.author.id,
        )


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
        if not inter.guild.voice_client.queue:
            return await inter.send_embed("Nothing in queue", ephemeral=True)

        toplay = inter.guild.voice_client.queue.pop(0)
        await inter.guild.voice_client.play(toplay)
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

        menu = QueueView(source=QueueSource(current, queue), ctx=inter)  # type: ignore
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
    ctx: MyContext


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
        if tracks[0] == self.queue[0]:
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
        if maximum > 1:
            c = sum((t.length / 1000 if t.length else 0) for t in self.queue)
            a = strftime("%H:%M:%S", gmtime(round(c)))
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{maximum} "
                f"({len(self.queue)} tracks - total {a})"
            )

        embed.set_author(name=self.title)

        return embed


class QueueView(ButtonMenuPages):
    def __init__(self, source: ListPageSource, ctx: MyContext | MyInter) -> None:
        super().__init__(source=source, style=ButtonStyle.blurple)
        self.ctx = ctx

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user and (
            interaction.user.id
            == (
                self.ctx.bot.owner_id
                if self.ctx
                else self.interaction.client.owner_id  # type: ignore
            )
            or interaction.user.id
            in (
                self.ctx.bot.owner_ids
                if self.ctx
                else self.interaction.client.owner_ids  # type: ignore
            )
        ):
            return True
        if self.ctx and self.ctx.command is not None:
            await interaction.response.send_message(
                f"This menu is for {self.ctx.author.mention}, "
                f"use {self.ctx.command.name} to have a menu to yourself.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"This menu is for {self.ctx.author.mention}.",
                ephemeral=True,
            )
        return False

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)

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
        elif inter.user.voice.channel.id != inter.guild.voice_client.channel.id:
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


class Music(Cog, name="music", description="Play some tunes with or without friends!"):
    def __init__(self, bot: MyBot):
        self.bot = bot

    def cog_check(self, ctx: MyContext) -> bool:
        assert ctx.command is not None
        if ctx.command.extras.get("bypass"):
            return True

        if (
            ctx.guild is None
            or isinstance(ctx.author, User)
            or isinstance(ctx.me, ClientUser)
        ):
            raise NoPrivateMessage()
        elif ctx.author.voice is None or ctx.author.voice.channel is None:
            raise NotInVoice()
        elif (
            not ctx.author.voice.channel.permissions_for(ctx.me).connect
            or not ctx.author.voice.channel.permissions_for(ctx.me).speak
        ) and not ctx.author.voice.channel.permissions_for(ctx.me).administrator:
            raise BotMissingPermissions(["connect", "speak"])
        elif ctx.voice_client is not None:
            if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
                raise NotInSameVoice()

        return True

    @property
    def emoji(self) -> str:
        return "🎵"

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.views_added:
            self.bot.add_view(PlayButton())
            self.bot.views_added = True

    @Cog.listener()
    async def on_pomice_track_end(self, player: Player, track: Track, _: str):
        await sleep(0.1)
        if player.is_playing:
            return

        if player.queue:
            toplay = player.queue.pop(0)

            await player.play(toplay)
            await playing_embed(toplay)
        else:
            await sleep(60)

            if not player.is_playing:
                assert track.ctx is not None

                if player is None or track.ctx.voice_client is None:
                    return

                await track.ctx.send_author_embed(  # type: ignore
                    "Disconnecting on no activity"
                )
                await player.destroy()

    @Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        await sleep(0.5)
        if (
            after.channel
            or not before.channel
            or not member.guild.voice_client
            or self.bot.user.id == member.id  # type: ignore
            or len(self.bot.listeners.get(before.channel.id, set())) > 0
        ):
            return

        await sleep(60)

        if len(self.bot.listeners.get(before.channel.id, set())) > 0:
            return

        if c := member.guild.voice_client.current:  # type: ignore
            await c.ctx.send_author_embed("Disconnecting on no listeners")

        await member.guild.voice_client.destroy()  # type: ignore

    @command(help="Join your voice channel.", aliases=["connect", "c", "j"])
    async def join(self, ctx: MyContext):
        assert (
            isinstance(ctx.author, Member)
            and ctx.author.voice is not None
            and ctx.author.voice.channel is not None
        )

        channel = ctx.author.voice.channel

        await channel.connect(cls=Player)  # type: ignore

        await ctx.send_author_embed(f"Connected to {channel.name}")

        self.bot.loop.create_task(self.leave_check(ctx))

    async def leave_check(self, ctx: MyContext):
        await sleep(60)

        if not ctx.voice_client:
            return

        if not ctx.voice_client.is_playing:
            await ctx.send_author_embed("Disconnecting on no activity")
            await ctx.voice_client.destroy()

    @command(help="Play some tunes!", aliases=["p"])
    async def play(self, ctx: MyContext, *, query: str):
        assert (
            isinstance(ctx.author, Member)
            and ctx.author.voice is not None
            and ctx.author.voice.channel is not None
        )

        if not ctx.voice_client:
            if cmd := self.bot.get_command("join"):
                await ctx.invoke(cmd)  # type: ignore

        await ctx.send(f"Searching `{query}`")

        player = ctx.voice_client
        result = await player.get_tracks(query=query, ctx=ctx)

        if not result:
            return await ctx.send_author_embed("No tracks found")

        if len(player.queue) >= 500:
            raise TooManyTracks()

        if not player.queue and not player.is_playing:
            if isinstance(result, Playlist):
                track = result.tracks[0]
                toplay = result.tracks[1:]
                info = result

                if len(player.queue) + len(toplay) > 500:
                    amount = 500 - len(player.queue)
                    await ctx.send_author_embed(f"Queueing {amount} tracks...")
            else:
                track = info = result[0]
                toplay = []

            await player.play(track=track)

            await playing_embed(info)
        else:
            if isinstance(result, Playlist):
                toplay = result.tracks
                info = result
                if len(player.queue) + len(toplay) > 500:
                    amount = 500 - len(player.queue)
                    await ctx.send_author_embed(f"Queueing {amount} tracks...")
            else:
                info = result[0]
                toplay = [result[0]]

            await playing_embed(info, queue=True)

        if toplay:
            player.queue += toplay

    @connected()
    @command(help="Pause the tunes", aliases=["hold"])
    async def pause(self, ctx: MyContext):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("No song is playing")
        await player.set_pause(True)
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000023f8\U0000fe0f")
        else:
            await ctx.send_author_embed("Paused")

    @connected()
    @command(help="Continue the bangers", aliases=["start"])
    async def resume(self, ctx: MyContext):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("No song is playing")
        await player.set_pause(False)
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000025b6\U0000fe0f")
        else:
            await ctx.send_author_embed("Resumed")

    @connected()
    @command(help="Stop, wait a minute...")
    async def stop(self, ctx: MyContext):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("No song is playing")
        player.queue = []
        await player.stop()
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000023f9\U0000fe0f")
        else:
            await ctx.send_author_embed("Stopped")

    @connected()
    @command(help="Bye bye :(", aliases=["die", "l", "leave", "d", "fuckoff"])
    async def disconnect(self, ctx: MyContext):
        player = ctx.voice_client
        await player.destroy()
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            if ctx.invoked_with == "die":
                await ctx.message.add_reaction("\U0001f480")
            elif ctx.invoked_with == "fuckoff":
                await ctx.message.add_reaction("\U00002639\U0000fe0f")
            else:
                await ctx.message.add_reaction("\U0001f44b")
        else:
            await ctx.send_author_embed("Bye :(")

    @connected()
    @command(help="Set volume")
    async def volume(self, ctx: MyContext, *, number: int):
        if not 1 <= number <= 500:
            return await ctx.reply("🚫 The allowed range is between 1 & 500")
        else:
            player = ctx.voice_client
            await player.set_volume(number)
            if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
                await ctx.message.add_reaction("\U0001f4e2")
            else:
                await ctx.send_author_embed(f"Volume set to `{number}%`")

    @command(help="Sing along to your favourite tunes!", extras={"bypass": True})
    async def lyrics(self, ctx: MyContext, *, query: str = ""):
        if not query:
            if ctx.voice_client is None or ctx.voice_client.current is None:
                raise MissingRequiredArgument(
                    param=signature(self.lyrics).parameters["query"]
                )

            assert ctx.voice_client.current.title is not None
            q = ctx.voice_client.current.title[:20]
        else:
            q = query
        data = {"q": q}
        headers = {"Authorization": f"Bearer {TKN}"}

        async with self.bot.session.get(API_URL, params=data, headers=headers) as resp:
            result = await resp.json()

        try:
            title = result["response"]["hits"][0]["result"]["title"]
            artist = result["response"]["hits"][0]["result"]["artist_names"]
            source = result["response"]["hits"][0]["result"]["url"]
            thumbnail = result["response"]["hits"][0]["result"]["header_image_url"]
        except IndexError:
            raise LyricsNotFound()

        a = await ctx.send("`Searching....`")

        async with self.bot.session.get(source) as resp:
            txt = await resp.text()

        lyricsform = [
            l.get_text("\n") + "\n"
            for l in BeautifulSoup(txt, "html.parser").select(
                "div[class*=Lyrics__Container]"
            )
        ]

        lyrics = "".join(lyricsform).replace("[", "\n[").strip()
        if len(lyrics) > 4096:
            lyrics = lyrics[:4093] + "..."

        embed = Embed(title=title, description=lyrics, color=self.bot.color)
        embed.set_author(name=artist)
        embed.set_thumbnail(url=thumbnail)
        await a.edit(embed=embed)

    @command(help="Hi :3")
    async def hello(self, ctx: MyContext):
        await ctx.send_author_embed("hey")

    @connected()
    @command(help="When the beat isnt hitting right", aliases=["s"])
    async def skip(self, ctx: MyContext):
        if not ctx.voice_client.queue:
            return await ctx.send_author_embed("Nothing in queue")

        toplay = ctx.voice_client.queue.pop(0)
        await ctx.voice_client.play(toplay)
        await playing_embed(toplay, skipped_by=ctx.author.mention)

    @connected()
    @command(help="Show the current beats", aliases=["np"])
    async def nowplaying(self, ctx: MyContext):
        if not ctx.voice_client.is_playing:
            return await ctx.send_author_embed("No song is playing")

        return await playing_embed(
            ctx.voice_client.current, length=True, override_ctx=ctx
        )

    @connected()
    @command(help="Switch things up")
    async def shuffle(self, ctx: MyContext):
        shuffle(ctx.voice_client.queue)

        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U0001f500")
        else:
            await ctx.send_author_embed("Shuffled the queue")

    @connected()
    @command(help="Show the queue of the beats", aliases=["q"])
    async def queue(self, ctx: MyContext):
        current = ctx.voice_client.current
        queue = ctx.voice_client.queue
        if not queue:
            return await ctx.send_author_embed("Nothing in queue")

        menu = QueueView(source=QueueSource(current, queue), ctx=ctx)
        await menu.start(ctx)

    @connected()
    @command(help="It hit so hard so you play it again")
    async def loop(self, ctx: MyContext):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("Nothing is playing")

        current = player.current
        player.queue.insert(0, current)
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U0001f502")
        else:
            await ctx.send_author_embed("Looping once")

    @connected()
    @command(help="Play one of your playlists", aliases=["ps"])
    async def playlists(self, ctx: MyContext):
        userid = self.bot.spotify_users.get(ctx.author.id, MISSING)

        if userid is MISSING:
            userid = await self.bot.db.fetchval(
                "SELECT spotify FROM users WHERE id=$1", ctx.author.id
            )
            self.bot.spotify_users[ctx.author.id] = userid

        if userid is None:
            return await ctx.send_embed(
                "Unlinked",
                f"You don't have a Spotify account linked, please use `{ctx.clean_prefix}spotify",
            )


def setup(bot: MyBot):
    bot.add_cog(Music(bot))
