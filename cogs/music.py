from __future__ import annotations

from typing import TYPE_CHECKING
from time import strftime, gmtime

from nextcord import ClientUser, Embed, Member, User
from nextcord.ext.commands import BotMissingPermissions, Cog, NoPrivateMessage, command
from pomice import Player, Playlist
from nextcord.utils import utcnow

from .extras.errors import NotInVoice
from .extras.types import MyContext

if TYPE_CHECKING:
    from ..mmain import MyBot


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

    @command(help="Play some tunes!", aliases=["p","Play"])
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
        assert player is not None
        result = await player.get_tracks(query=query, ctx=ctx)

        if not result:
            return await ctx.send_embed("No tracks found", "No tracks were found.")

        if isinstance(result, Playlist):
            track = result.tracks[0]
        else:
            track = result[0]

        await player.play(track=track)

        embed = Embed(
            title=track.info["title"],
            description=f"{strftime('%H:%M:%S', gmtime(track.info['length'] / 1000))}",
            color=self.bot.color,
            timestamp=utcnow(),
        )
        embed.set_author(name=track.info["author"], url=track.info["uri"])

        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)

        await ctx.send("Now playing", embed=embed)
    @command(help="Pause a song",aliases=["hold","Pause"])
    async def pause(self,ctx: MyContext):
        player = ctx.voice_client
        await player.set_pause(True)
        await ctx.send("Paused")

    @command(help="resume",aliases=["start","Resume"])
    async def resume(self,ctx: MyContext):
        player = ctx.voice_client
        await player.set_pause(False)
        await ctx.send("Resumed")

    @command(help="stop a song",aliases=["s","Stop"])
    async def stop(self,ctx: MyContext):
        player = ctx.voice_client
        await player.stop()
        await ctx.send("stopped")

    @command(help="Set volume")
    async def volume(self,ctx:MyContext,*,number:int):
        if 1>number> 100:
            await ctx.reply("🚫 The allowed range is between 1 & 100")
            return
        else:
            player = ctx.voice_client
            await player.set_volume(number)
            await ctx.send(f"Volume set to {number}%")

def setup(bot: MyBot):
    bot.add_cog(Music(bot))
