from __future__ import annotations

from typing import TYPE_CHECKING
from time import strftime, gmtime
from asyncio import sleep

from nextcord import ClientUser, Embed, Member, User
from nextcord.ext.commands import (
    BotMissingPermissions,
    Cog,
    NoPrivateMessage,
    command,
    Context,
    check,
)
from pomice import Playlist
from nextcord.utils import utcnow

from .extras.errors import NotInVoice, TooManyTracks
from .extras.types import MyContext, Player

if TYPE_CHECKING:
    from pomice import Track

    from ..mmain import MyBot


def connected():
    async def extended_check(ctx: Context) -> bool:
        if ctx.voice_client is None:
            if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
                await ctx.message.add_reaction("\U0000274c")
            else:
                await ctx.send("I'm not even connected")

            return False

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
    async def on_track_end(self, player: Player, track: Track, reason: str):
        if player.queue:
            toplay = player.queue.pop(0)

            await player.play(toplay)
        else:
            await sleep(60)

            if not player.is_playing:
                assert track.ctx is not None

                await track.ctx.send("Disconnecting on timeout \U0001f44b")
                await player.destroy()

    async def playing_embed(self, track: Track | Playlist, queue: bool):
        if isinstance(track, Playlist):
            assert track.tracks[0].ctx is not None

            ctx = track.tracks[0].ctx

            title = track.name
            author = ", ".join({t.author for t in track.tracks if t.author is not None})
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
            time = strftime(
                "%H:%M:%S",
                gmtime(track.length if track.length is not None else 0 / 1000),
            )

        embed = Embed(
            title=title,
            description=f"{time} - requested by {ctx.author.display_name}",
            color=self.bot.color,
            timestamp=utcnow(),
        )
        embed.set_author(name=author, url=track.uri)

        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)

        if queue:
            await ctx.send("Queued", embed=embed)
        else:
            await ctx.send("Now Playing", embed=embed)

    @command(help="Join your voice channel.", aliases=["connect", "c", "j"])
    async def join(self, ctx: MyContext):
        assert (
            isinstance(ctx.author, Member)
            and ctx.author.voice is not None
            and ctx.author.voice.channel is not None
        )

        channel = ctx.author.voice.channel

        await channel.connect(cls=Player)  # type: ignore

        await ctx.send_embed("Connected", f"I have connected to {channel.mention}!")

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
            return await ctx.send_embed("No tracks found", "No tracks were found.")

        if not player.queue:
            if isinstance(result, Playlist):
                track = result.tracks[0]
                toplay = result.tracks[1:]
                info = result
            else:
                track = info = result[0]
                toplay = []

            await player.play(track=track)

            await self.playing_embed(info, queue=False)
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
            await ctx.send("Paused")

    @connected()
    @command(help="Continue the bangers", aliases=["start"])
    async def resume(self, ctx: MyContext):
        player = ctx.voice_client
        await player.set_pause(False)
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000025b6\U0000fe0f")
        else:
            await ctx.send("Resumed")

    @connected()
    @command(help="Stop, wait a minute...", aliases=["s"])
    async def stop(self, ctx: MyContext):
        player = ctx.voice_client
        await player.stop()
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            await ctx.message.add_reaction("\U000023f9\U0000fe0f")
        else:
            await ctx.send("Stopped")

    @connected()
    @command(help="Bye bye :(", aliases=["die", "l", "leave", "d", "fuck off"])
    async def disconnect(self, ctx: MyContext):
        player = ctx.voice_client
        await player.destroy()
        if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
            if ctx.invoked_with == "die":
                await ctx.message.add_reaction("\U0001f480")
            elif ctx.invoked_with == "fuck off":
                await ctx.message.add_reaction("\U00002639\U0000fe0f")
            else:
                await ctx.message.add_reaction("\U0001f44b")
        else:
            await ctx.send("Bye :(")

    @connected()
    @command(help="Set volume")
    async def volume(self, ctx: MyContext, *, number: int):
        if not 1 < number < 500:
            return await ctx.reply("🚫 The allowed range is between 1 & 500")
        else:
            player = ctx.voice_client
            await player.set_volume(number)
            if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
                await ctx.message.add_reaction("\U0001f4e2")
            else:
                await ctx.send(f"Volume set to `{number}%`")

    @connected()
    @command(help="disconnect from voice channel",aliases=["dis","fuck off","leave"])
    async def disconnect(self,ctx:MyContext):
        channel = ctx.author.voice.channel
        await channel.disconnect(cls=Player)


def setup(bot: MyBot):
    bot.add_cog(Music(bot))
