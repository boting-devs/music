from __future__ import annotations

from asyncio import sleep
from random import shuffle
from functools import partial
from logging import getLogger
from typing import TYPE_CHECKING, Union

from pomice import Playlist
from bs4 import BeautifulSoup
from nextcord.utils import MISSING
from nextcord.ui import Button, Select
from nextcord import ClientUser, Embed, Member, SlashOption, User, slash_command
from nextcord.ext.commands import BotMissingPermissions, Cog, NoPrivateMessage, command
from botbase import MyContext as BBMyContext, MyInter as BBMyInter

from .extras.checks import connected
from .extras.views import PlaylistView, QueueView, QueueSource, PlayButton
from .extras.playing_embed import playing_embed
from .extras.types import MyContext, MyInter, Player
from .extras.errors import (
    LyricsNotFound,
    NotInSameVoice,
    NotInVoice,
    SongNotProvided,
    TooManyTracks,
)

if TYPE_CHECKING:
    from pomice import Track
    from nextcord import VoiceState

    from ..mmain import MyBot


log = getLogger(__name__)

API_URL = "https://api.genius.com/search/"
TKN = "E4Eq5BhA2Xq6U99o1swO5IWcS7BBKyx1lCzyApT1wbyEqhItNaK5PpukKpUKrt3G"
TEST = [802586580766162964, 939509053623795732]


class Music(Cog, name="music", description="Play some tunes with or without friends!"):
    BYPASS = ("lyrics",)

    def __init__(self, bot: MyBot):
        self.bot = bot

    def cog_application_command_check(self, ctx: MyInter) -> bool:
        return self.cog_check(ctx)

    def cog_check(self, ctx: MyContext | MyInter) -> bool:
        cmd = str(ctx.command)

        if cmd in self.BYPASS:
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

        async def task():
            await sleep(60)

            assert before.channel

            if len(self.bot.listeners.get(before.channel.id, set())) > 0:
                self.bot.listener_tasks.pop(member.guild.id)
                return

            if c := member.guild.voice_client.current:  # type: ignore
                await c.ctx.send_author_embed("Disconnecting on no listeners")

            await member.guild.voice_client.destroy()  # type: ignore

            self.bot.listener_tasks.pop(member.guild.id)

        t = self.bot.loop.create_task(task())
        self.bot.listener_tasks[member.guild.id] = t

    @slash_command(name="join", description="Make me join your voice channel!")
    async def join_(self, ctx: MyInter):
        return await self.join(ctx)  # type: ignore

    @command(help="Join your voice channel.", aliases=["connect", "c", "j"])
    async def join(self, ctx: Union[MyContext, MyInter]):
        assert (
            isinstance(ctx.author, Member)
            and ctx.author.voice is not None
            and ctx.author.voice.channel is not None
        )

        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            if channel.id == ctx.voice_client.channel.id:
                return await ctx.reply("Already Connected!")

        await channel.connect(cls=Player)  # type: ignore

        await ctx.send_author_embed(f"Connected to {channel.name}")

        self.bot.loop.create_task(self.leave_check(ctx))

    async def leave_check(self, ctx: MyContext | MyInter):
        await sleep(60)

        if not ctx.voice_client:
            return

        if not ctx.voice_client.is_playing:
            await ctx.send_author_embed("Disconnecting on no activity")
            await ctx.voice_client.destroy()

    @slash_command(name="play", description="Play some tunes!")
    async def play_(
        self, ctx: MyInter, query: str = SlashOption(description="Query/link to search")
    ):
        return await self.play(ctx, query=query)  # type: ignore

    @command(help="Play some tunes!", aliases=["p"])
    async def play(self, ctx: Union[MyContext, MyInter], *, query: str):
        assert (
            isinstance(ctx.author, Member)
            and ctx.author.voice is not None
            and ctx.author.voice.channel is not None
        )

        if not ctx.voice_client:
            await self.join(ctx)  # type: ignore

        if isinstance(ctx, BBMyInter) and ctx.response.is_done():
            await ctx.channel.send(f"Searching `{query}`")  # type: ignore
        else:
            await ctx.send(f"Searching `{query}`")

        player = ctx.voice_client
        result = await player.get_tracks(query=query, ctx=ctx)  # type: ignore

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
    @slash_command(name="pause", description="Pause the tunes")
    async def pause_(self, ctx: MyInter):
        return await self.pause(ctx)  # type: ignore

    @connected()
    @command(help="Pause the tunes", aliases=["hold"])
    async def pause(self, ctx: Union[MyContext, MyInter]):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("No song is playing")
        await player.set_pause(True)

        if isinstance(ctx, BBMyContext) and ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000023f8\U0000fe0f")
        else:
            await ctx.send_author_embed("Paused")

    @connected()
    @slash_command(name="resume", description="Continue the bangers")
    async def resume_(self, ctx: MyInter):
        return await self.resume(ctx)  # type: ignore

    @connected()
    @command(help="Continue the bangers", aliases=["start"])
    async def resume(self, ctx: Union[MyContext, MyInter]):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("No song is playing")
        await player.set_pause(False)

        if isinstance(ctx, BBMyContext) and ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000025b6\U0000fe0f")
        else:
            await ctx.send_author_embed("Resumed")

    @connected()
    @slash_command(name="stop", description="Sto, wait a minute...")
    async def stop_(self, ctx: MyInter):
        return await self.stop(ctx)  # type: ignore

    @connected()
    @command(help="Stop, wait a minute...")
    async def stop(self, ctx: Union[MyContext, MyInter]):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("No song is playing")
        player.queue = []
        await player.stop()

        if isinstance(ctx, BBMyContext) and ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000023f9\U0000fe0f")
        else:
            await ctx.send_author_embed("Stopped")

    @connected()
    @slash_command(name="disconnect", description="Bye bye :(")
    async def disconnect_(self, ctx: MyInter):
        return await self.disconnect(ctx)  # type: ignore

    @connected()
    @command(help="Bye bye :(", aliases=["die", "l", "leave", "d", "fuckoff"])
    async def disconnect(self, ctx: MyContext):
        player = ctx.voice_client
        await player.destroy()

        if isinstance(ctx, BBMyContext) and ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            if ctx.invoked_with == "die":
                await ctx.message.add_reaction("\U0001f480")
            elif ctx.invoked_with == "fuckoff":
                await ctx.message.add_reaction("\U00002639\U0000fe0f")
            else:
                await ctx.message.add_reaction("\U0001f44b")
        else:
            await ctx.send_author_embed("Bye :(")

    @connected()
    @slash_command(name="volume", description="Turn up the beats")
    async def volume_(
        self,
        ctx: MyInter,
        volume: int = SlashOption(
            description="Volume, in %", min_value=1, max_value=500
        ),
    ):
        return await self.volume(ctx, number=volume)  # type: ignore

    @connected()
    @command(help="Turn up the beats")
    async def volume(self, ctx: Union[MyContext, MyInter], *, number: int):
        if not 1 <= number <= 500:
            return await ctx.send("🚫 The allowed range is between 1 & 500")
        else:
            player = ctx.voice_client
            await player.set_volume(number)

            if isinstance(ctx, BBMyContext) and ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
                await ctx.message.add_reaction("\U0001f4e2")
            else:
                await ctx.send_author_embed(f"Volume set to `{number}%`")

    @slash_command(name="lyrics", description="Sing along to your favourite tunes!")
    async def lyrics_(
        self,
        ctx: MyInter,
        query: str = SlashOption(description="Song name", required=False),
    ):
        return await self.lyrics(ctx, query=query)  # type: ignore

    @command(help="Sing along to your favourite tunes!")
    async def lyrics(self, ctx: Union[MyContext, MyInter], *, query: str = ""):
        if not query:
            if ctx.voice_client is None or ctx.voice_client.current is None:
                raise SongNotProvided()

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

        if a is not None:
            await a.edit(embed=embed)
        elif not isinstance(ctx, BBMyContext):
            await ctx.edit_original_message(embed=embed)

    @connected()
    @slash_command(name="skip", description="When the beat isn't hitting right")
    async def skip_(self, ctx: MyInter):
        return await self.skip(ctx)  # type: ignore

    @connected()
    @command(help="When the beat isn't hitting right", aliases=["s"])
    async def skip(self, ctx: Union[MyContext, MyInter]):
        if not ctx.voice_client.queue:
            return await ctx.send_author_embed("Nothing in queue")

        toplay = ctx.voice_client.queue.pop(0)
        await ctx.voice_client.play(toplay)
        await playing_embed(toplay, skipped_by=ctx.author.mention, override_ctx=ctx)

    @connected()
    @slash_command(name="nowplaying", description="Show the current beats")
    async def nowplaying_(self, ctx: MyInter):
        return await self.nowplaying(ctx)  # type: ignore

    @connected()
    @command(help="Show the current beats", aliases=["np"])
    async def nowplaying(self, ctx: Union[MyContext, MyInter]):
        if not ctx.voice_client.is_playing:
            return await ctx.send_author_embed("No song is playing")

        return await playing_embed(
            ctx.voice_client.current, length=True, override_ctx=ctx
        )

    @connected()
    @slash_command(name="shuffle", description="Switch things up")
    async def shuffle_(self, ctx: MyInter):
        return await self.shuffle(ctx)  # type: ignore

    @connected()
    @command(help="Switch things up")
    async def shuffle(self, ctx: Union[MyContext, MyInter]):
        shuffle(ctx.voice_client.queue)

        if isinstance(ctx, BBMyContext) and ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U0001f500")
        else:
            await ctx.send_author_embed("Shuffled the queue")

    @connected()
    @slash_command(name="queue", description="Show the queue of tunes")
    async def queue_(self, ctx: MyInter):
        return await self.queue(ctx)  # type: ignore

    @connected()
    @command(help="Show the queue of the beats", aliases=["q"])
    async def queue(self, ctx: Union[MyContext, MyInter]):
        current = ctx.voice_client.current
        queue = ctx.voice_client.queue
        if not queue:
            return await ctx.send_author_embed("Nothing in queue")

        menu = QueueView(source=QueueSource(current, queue), ctx=ctx)
        if isinstance(ctx, MyInter):
            await menu.start(interaction=ctx)
        else:
            await menu.start(ctx)

    @connected()
    @slash_command(name="loop", description="It hit so hard you play it again")
    async def loop_(self, inter: MyInter):
        return await self.loop(inter)  # type: ignore

    @connected()
    @command(help="It hit so hard so you play it again")
    async def loop(self, ctx: Union[MyContext, MyInter]):
        player = ctx.voice_client
        if not player.is_playing:
            return await ctx.send_author_embed("Nothing is playing")

        current = player.current
        player.queue.insert(0, current)

        if isinstance(ctx, BBMyContext) and ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U0001f502")
        else:
            await ctx.send_author_embed("Looping once")

    @connected()
    @slash_command(
        name="playlists",
        description="Play one of your amazing playlists",
    )
    async def playlists_(self, inter: MyInter):
        return await self.playlists(inter)  # type: ignore

    @command(help="Play one of your playlists", aliases=["ps"])
    async def playlists(self, ctx: Union[MyContext, MyInter]):
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

        loop = self.bot.loop
        sp = self.bot.spotipy

        all_playlists = []
        count = 0
        total = 25

        while count < total:
            func = partial(sp.user_playlists, userid, limit=50, offset=count)
            playlists = await loop.run_in_executor(None, func)
            if playlists is None:
                return await ctx.send_embed(
                    "Error", "Something went wrong, could not find your playlists"
                )

            count += len(playlists["items"])
            all_playlists += playlists["items"]
            total = playlists["total"]

        if not len(all_playlists):
            return await ctx.send_embed(
                "No playlists",
                "**You do not have any public playlists!** \nPlease refer this to make your playlist public- https://www.androidauthority.com/make-spotify-playlist-public-3075538/",
            )

        view = PlaylistView(all_playlists)

        m = await ctx.send("Choose a public playlist", view=view)
        if not m and isinstance(ctx, BBMyInter):
            m = await ctx.original_message()

        assert m is not None

        view.message = m

        await view.wait()

        if view.uri is None:
            for child in view.children:
                if isinstance(child, (Button, Select)):
                    child.disabled = True

            return await view.message.edit(content="You took too long...", view=view)

        await self.play(ctx, query=view.uri)  # type: ignore

    @command()
    async def save(self,ctx: Union[MyContext, MyInter]):
        if not ctx.voice_client.is_playing:
            return await ctx.send_author_embed("No song is playing")

        await ctx.author.send(embed = playing_embed
        )



def setup(bot: MyBot):
    bot.add_cog(Music(bot))
