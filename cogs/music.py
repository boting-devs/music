from __future__ import annotations

from asyncio import sleep
from logging import getLogger
from time import gmtime, strftime
from typing import TYPE_CHECKING

from nextcord import ClientUser, Embed, Member, User, ButtonStyle, Interaction
from nextcord.ext.commands import (
    BotMissingPermissions,
    Cog,
    Context,
    NoPrivateMessage,
    check,
    command,
)
from nextcord.utils import utcnow
from nextcord.ui import button, Button, View
from pomice import Playlist
from botbase import MyInter

from .extras.errors import NotConnected, NotInVoice, TooManyTracks
from .extras.types import MyContext, Player
import aiohttp

from bs4 import BeautifulSoup
from requests import get
if TYPE_CHECKING:
    from pomice import Track

    from ..mmain import MyBot


log = getLogger(__name__)

API_URL = 'https://api.genius.com/search/'
TKN = "E4Eq5BhA2Xq6U99o1swO5IWcS7BBKyx1lCzyApT1wbyEqhItNaK5PpukKpUKrt3G"
def connected():
    async def extended_check(ctx: Context) -> bool:
        if ctx.voice_client is None:
            raise NotConnected()

        return True

    return check(extended_check)


class PlayButon(View):
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
            not inter.guild
            or not inter.guild.voice_client
            or not inter.user.id
            in [m.id for m in inter.guild.voice_client.channel.members]  # type: ignore
        ):
            await inter.send_embed(
                "Not in Voice", "You need to be in the same vc as the bot!", ephemeral=True
            )
            return False

        return True

    @button(
        emoji="\U000023f8\U0000fe0f", style=ButtonStyle.blurple, custom_id="view:pp"
    )
    async def playpause(self, button: Button, inter: Interaction):
        assert inter.guild is not None
        assert inter.guild.voice_client is not None
        assert isinstance(inter.guild.voice_client, Player)

        if not inter.guild.voice_client.is_paused:
            await inter.guild.voice_client.set_pause(True)
            button.emoji = "\U000025b6\U0000fe0f"
            await inter.response.edit_message(view=self)
        else:
            await inter.guild.voice_client.set_pause(False)
            button.emoji = "\U000023f8\U0000fe0f"
            await inter.response.edit_message(view=self)


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
    async def on_ready(self):
        if not self.bot.views_added:
            self.bot.add_view(PlayButon())
            self.bot.views_added = True

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
        view = PlayButon()
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
            await ctx.send(embed=embed, content="Queued", view=view)
        else:
            await ctx.send(embed=embed, view=view)

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
        @command(help="Sing along to your favourite tunes!")
        async def lyrics(self, ctx: MyContext, *,search):
            data = {'q': search}
            headers = {'Authorization': f'Bearer {TKN}'}
            try:
                result = get(API_URL, params=data, headers=headers).json()
                
            except Exception as exc:
                await ctx.send(f'Could not get lyrics, as a error occured: {exc}')
                
            
            title = result['response']['hits'][0]['result']['title']
            artist = result['response']['hits'][0]['result']['artist_names']
            source = result['response']['hits'][0]['result']['url']
            thumbnail = result['response']['hits'][0]['result']['header_image_url']
            
            lyricsform = []
            for lyricsdata in BeautifulSoup(get(source).text, 'html.parser').select('div[class*=Lyrics__Container]'):
                dat = lyricsdata.get_text('\n')
                lyricsform.append(f"{dat}\n")
                
            lyrics = ''.join(lyricsform).replace('[', '\n[').strip()
            
            await ctx.send_author_embed(lyrics)
def setup(bot: MyBot):
    bot.add_cog(Music(bot))
