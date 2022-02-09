from __future__ import annotations

from asyncio import sleep
from logging import getLogger
from time import gmtime, strftime
from typing import TYPE_CHECKING

from nextcord import ClientUser, Embed, Member, User
from nextcord.ext.commands import (
    BotMissingPermissions,
    Cog,
    Context,
    NoPrivateMessage,
    check,
    command,
)
from nextcord.utils import utcnow
from pomice import Playlist

from .extras.errors import NotConnected, NotInVoice, TooManyTracks
from .extras.types import MyContext, Player
import aiohttp

if TYPE_CHECKING:

    from pomice import Track

    from ..mmain import MyBot


log = getLogger(__name__)


def connected():
    async def extended_check(ctx: Context) -> bool:
        if ctx.voice_client is None:
            raise NotConnected()

        return True

    return check(extended_check)


class Music(Cog, name="music", description="Play some tunes with or without friends!"):
    def __init__(self, bot: MyBot):
        self.bot = bot

    def cog_check(self, ctx: MyContext) -> bool:
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

        return True

    @Cog.listener()
    async def on_pomice_track_end(self, player: Player, track: Track, _: str):
        if player.queue:
            toplay = player.queue.pop(0)

            await player.play(toplay)
        else:
            await sleep(60)

            if not player.is_playing:
                assert track.ctx is not None

                await track.ctx.send_author_embed("Disconnecting on no activity")  # type: ignore
                await player.destroy()

    async def playing_embed(self, track: Track | Playlist, queue: bool = False):
        if isinstance(track, Playlist):
            assert track.tracks[0].ctx is not None

            ctx = track.tracks[0].ctx

            title = track.name
            author = "Multiple Authors"
            time = strftime(
                "%H:%M:%S",
                gmtime(
                    sum(t.length for t in track.tracks if t.length is not None) / 1000
                ),
            )
        else:
            assert track.ctx is not None

            ctx = track.ctx
            title = track.title
            author = track.author
            if not track.length:
                time = "Unknown"
            else:
                time = strftime(
                    "%H:%M:%S",
                    gmtime(track.length / 1000),
                )

        embed = Embed(
            description=f"{time} - {ctx.author.mention}",
            color=self.bot.color,
            timestamp=utcnow(),
        )
        embed.set_author(name=str(title) + " - " + str(author), url=track.uri)

        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)

        if queue:
            await ctx.send(embed=embed, content="Queued")
        else:
            await ctx.send(embed=embed)

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

        if not ctx.voice_client or not ctx.voice_client.is_playing:
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

        player = ctx.voice_client
        result = await player.get_tracks(query=query, ctx=ctx)

        if not result:
            return await ctx.send_author_embed("No tracks found")

        if not player.queue and not player.is_playing:
            if isinstance(result, Playlist):
                track = result.tracks[0]
                toplay = result.tracks[1:]
                info = result
            else:
                track = info = result[0]
                toplay = []

            await player.play(track=track)

            await self.playing_embed(info)
        else:
            if isinstance(result, Playlist):
                toplay = result.tracks
                info = result
            else:
                info = result[0]
                toplay = [result[0]]

            await self.playing_embed(info, queue=True)

        if len(player.queue) + len(toplay) > 100:
            raise TooManyTracks()

        if toplay:
            player.queue += toplay

    @connected()
    @command(help="Pause the tunes", aliases=["hold"])
    async def pause(self, ctx: MyContext):
        player = ctx.voice_client
        await player.set_pause(True)
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000023f8\U0000fe0f")
        else:
            await ctx.send_author_embed("Paused")

    @connected()
    @command(help="Continue the bangers", aliases=["start"])
    async def resume(self, ctx: MyContext):
        player = ctx.voice_client
        await player.set_pause(False)
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000025b6\U0000fe0f")
        else:
            await ctx.send_author_embed("Resumed")

    @connected()
    @command(help="Stop, wait a minute...", aliases=["s"])
    async def stop(self, ctx: MyContext):
        player = ctx.voice_client
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

    @connected()
    @command(help="Lyrics")
    async def lyrics(self,ctx: MyContext):
        current_track=ctx.voice_client.current
        print(current_track)
        author = current_track.author
        Lyric_url = "https://some-random-api.ml/lyrics?title="

        async with ctx.typing:
            async with aiohttp.request("GET",Lyric_url+current_track,headers={}) as r:
                if not 300 > r.status >= 200:
                    return await ctx.send("No lyrics")

                data = await r.json()

                if len(data["lyrics"]) > 2000:
                    return await ctx.send(f"<{data['links']['genius']}>")

                embed = Embed(
                    title=data["title"],
                    description=data["lyrics"],
                    color=self.bot.color,
                    timestamp=utcnow())
                embed.set_thumbnail(url=current_track.thumbnail)
                await ctx.send(embed=embed)
def setup(bot: MyBot):
    bot.add_cog(Music(bot))
