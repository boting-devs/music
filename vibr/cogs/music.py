from __future__ import annotations

from asyncio import sleep
from functools import partial
from logging import getLogger
from random import shuffle
from time import gmtime, strftime
from typing import TYPE_CHECKING

from botbase import MyInter as BBMyInter
from bs4 import BeautifulSoup
from nextcord import (
    ClientUser,
    Embed,
    Member,
    PartialInteractionMessage,
    User,
    slash_command,
)
from nextcord.ext.application_checks import (
    ApplicationBotMissingPermissions as BotMissingPermissions,
)
from nextcord.ext.commands import Cog
from nextcord.ui import Button, Select
from nextcord.utils import MISSING, utcnow

from pomice import Playlist,Equalizer

from .extras.checks import connected
from .extras.errors import (
    Ignore,
    LyricsNotFound,
    NotInSameVoice,
    NotInVoice,
    SongNotProvided,
    TooManyTracks,
)
from .extras.playing_embed import playing_embed
from .extras.types import MyInter, Player
from .extras.views import PlayButton, PlaylistView, QueueSource, QueueView

if TYPE_CHECKING:
    from nextcord import VoiceState
    from pomice import Track

    from ..__main__ import Vibr


log = getLogger(__name__)

API_URL = "https://api.genius.com/search/"
TKN = "E4Eq5BhA2Xq6U99o1swO5IWcS7BBKyx1lCzyApT1wbyEqhItNaK5PpukKpUKrt3G"
TEST = [802586580766162964, 939509053623795732]


class Music(Cog, name="music", description="Play some tunes with or without friends!"):
    BYPASS = ("lyrics",)

    def __init__(self, bot: Vibr):
        self.bot = bot

    def cog_application_command_check(self, inter: MyInter) -> bool:
        cmd = inter.application_command.qualified_name  # type: ignore

        if cmd in self.BYPASS:
            return True

        if (
            inter.guild is None
            or isinstance(inter.user, User)
            or isinstance(inter.me, ClientUser)
        ):
            raise Ignore()
        elif inter.user.voice is None or inter.user.voice.channel is None:
            raise NotInVoice()
        elif (
            not inter.user.voice.channel.permissions_for(inter.me).connect
            or not inter.user.voice.channel.permissions_for(inter.me).speak
        ) and not inter.user.voice.channel.permissions_for(inter.me).administrator:
            raise BotMissingPermissions(["connect", "speak"])
        elif inter.guild.voice_client is not None:
            if inter.user.voice.channel.id != inter.guild.voice_client.channel.id:
                raise NotInSameVoice()

        return True

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
            if (
                player.channel.guild.id in self.bot.whitelisted_guilds
                and self.bot.whitelisted_guilds[player.channel.guild.id] > utcnow()
            ):
                return

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

        if (
            member.guild.id in self.bot.whitelisted_guilds
            and self.bot.whitelisted_guilds[member.guild.id] > utcnow()
        ):
            return

        async def task():
            await sleep(60)

            assert before.channel

            if len(self.bot.listeners.get(before.channel.id, set())) > 0:
                self.bot.listener_tasks.pop(member.guild.id, None)
                return

            if not member.guild.voice_client:
                self.bot.listener_tasks.pop(member.guild.id, None)
                return

            if c := member.guild.voice_client.current:  # type: ignore
                await c.ctx.send_author_embed("Disconnecting on no listeners")

            await member.guild.voice_client.destroy()  # type: ignore

            self.bot.listener_tasks.pop(member.guild.id, None)

        t = self.bot.loop.create_task(task())
        self.bot.listener_tasks[member.guild.id] = t

    @slash_command(dm_permission=False)
    async def join(self, inter: MyInter):
        """Join your voice channel!"""

        assert (
            isinstance(inter.user, Member)
            and inter.user.voice is not None
            and inter.user.voice.channel is not None
        )

        channel = inter.user.voice.channel
        if inter.guild.voice_client is not None:
            if channel.id == inter.guild.voice_client.channel.id:
                return await inter.reply("Already Connected!")

        await channel.connect(cls=Player)

        await inter.send_author_embed(f"Connected to {channel.name}")

        self.bot.loop.create_task(self.leave_check(inter))

    async def leave_check(self, inter: MyInter):
        if (
            inter.guild.id in self.bot.whitelisted_guilds
            and self.bot.whitelisted_guilds[inter.guild.id] > utcnow()
        ):
            return

        async def task():
            await sleep(60)

            if not inter.guild.voice_client:
                self.bot.activity_tasks.pop(inter.guild.id, None)
                return

            if not inter.guild.voice_client.is_playing:
                await inter.send_author_embed("Disconnecting on no activity")
                await inter.guild.voice_client.destroy()

            self.bot.activity_tasks.pop(inter.guild.id, None)

        t = self.bot.loop.create_task(task())
        self.bot.activity_tasks[inter.guild.id] = t

    @Cog.listener()
    async def on_application_command_completion(self, inter: MyInter):
        if (
            inter.application_command
            and inter.application_command.parent_cog
            and inter.application_command.parent_cog.qualified_name  # type: ignore
            == self.qualified_name
        ):
            self.bot.activity_tasks.pop(inter.guild.id, None)

    @slash_command(dm_permission=False)
    async def play(self, inter: MyInter, *, query: str):
        """Play some tunes!"""

        assert (
            isinstance(inter.user, Member)
            and inter.user.voice is not None
            and inter.user.voice.channel is not None
        )

        if not inter.guild.voice_client:
            await self.join(inter)

        await inter.send(f"Searching `{query}`")

        player = inter.guild.voice_client
        result = await player.get_tracks(query=query, ctx=inter)  # type: ignore

        if not result:
            return await inter.send_author_embed("No tracks found")

        if len(player.queue) >= 500:
            raise TooManyTracks()

        if not player.queue and not player.is_playing:
            if isinstance(result, Playlist):
                track = result.tracks[0]
                toplay = result.tracks[1:]
                info = result

                if len(player.queue) + len(toplay) > 500:
                    amount = 500 - len(player.queue)
                    await inter.send_author_embed(f"Queueing {amount} tracks...")
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
                    await inter.send_author_embed(f"Queueing {amount} tracks...")
            else:
                info = result[0]
                toplay = [result[0]]

            await playing_embed(info, queue=True)

        if toplay:
            player.queue += toplay

    @connected()
    @slash_command(dm_permission=False)
    async def pause(self, inter: MyInter):
        """Pause the tunes"""

        player = inter.guild.voice_client
        if not player.is_playing:
            return await inter.send_author_embed("No song is playing")

        await player.set_pause(True)

        await inter.send_author_embed("Paused")

    @connected()
    @slash_command(dm_permission=False)
    async def resume(self, inter: MyInter):
        """Continue the bangers!"""

        player = inter.guild.voice_client
        if not player.is_playing:
            return await inter.send_author_embed("No song is playing")

        await player.set_pause(False)

        await inter.send_author_embed("Resumed")

    @connected()
    @slash_command(dm_permission=False)
    async def stop(self, inter: MyInter):
        """Stop, wait a minute..."""

        player = inter.guild.voice_client
        if not player.is_playing:
            return await inter.send_author_embed("No song is playing")

        player.queue = []
        await player.stop()

        await inter.send_author_embed("Stopped")

    @connected()
    @slash_command(dm_permission=False)
    async def disconnect(self, inter: MyInter):
        """Bye bye :("""

        player = inter.guild.voice_client
        await player.destroy()

        await inter.send_author_embed("Bye :(")

    @connected()
    @slash_command(dm_permission=False)
    async def volume(self, inter: MyInter, *, number: int):
        """Turn up the beats"""

        if not 1 <= number <= 500:
            return await inter.send("🚫 The allowed range is between 1 & 500")

        player = inter.guild.voice_client
        await player.set_volume(number)

        await inter.send_author_embed(f"Volume set to `{number}%`")

    @slash_command(dm_permission=False)
    async def lyrics(self, inter: MyInter, *, query: str = ""):
        """Sing along to your favourite tunes!"""

        if not query:
            if (
                inter.guild.voice_client is None
                or inter.guild.voice_client.current is None
            ):
                raise SongNotProvided()

            assert inter.guild.voice_client.current.title is not None
            q = inter.guild.voice_client.current.title[:20]
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

        a = await inter.send("`Searching....`")

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

    @connected()
    @slash_command(dm_permission=False)
    async def skip(self, inter: MyInter):
        """When the beat isn't hitting right"""

        if not inter.guild.voice_client.queue:
            player = inter.guild.voice_client
            await player.stop()
            return await inter.send_author_embed("Nothing in queue. Stopping the music")

        toplay = inter.guild.voice_client.queue.pop(0)
        await inter.guild.voice_client.play(toplay)
        await playing_embed(toplay, skipped_by=inter.user.mention, override_inter=inter)

    @connected()
    @slash_command(name="now-playing", dm_permission=False)
    async def now_playing(self, inter: MyInter):
        """Show the current beats."""

        if not inter.guild.voice_client.is_playing:
            return await inter.send_author_embed("No song is playing")

        return await playing_embed(
            inter.guild.voice_client.current, length=True, override_inter=inter
        )

    @connected()
    @slash_command(dm_permission=False)
    async def shuffle(self, inter: MyInter):
        """Switch things up"""

        shuffle(inter.guild.voice_client.queue)

        await inter.send_author_embed("Shuffled the queue")

    @connected()
    @slash_command(dm_permission=False)
    async def queue(self, inter: MyInter):
        """Show the queue of the beats."""

        current = inter.guild.voice_client.current
        queue = inter.guild.voice_client.queue
        if not queue:
            return await inter.send_author_embed("Nothing in queue")

        menu = QueueView(source=QueueSource(current, queue), inter=inter)

        await menu.start(interaction=inter)

    @connected()
    @slash_command(dm_permission=False)
    async def loop(self, inter: MyInter):
        """It hit so hard so you play it again"""

        player = inter.guild.voice_client
        if not player.is_playing:
            return await inter.send_author_embed("Nothing is playing")

        current = player.current
        player.queue.insert(0, current)

        await inter.send_author_embed("Looping once")

    @slash_command(dm_permission=False)
    async def playlists(self, inter: MyInter):
        """Play one of your spotify playlists."""

        userid = self.bot.spotify_users.get(inter.user.id, MISSING)

        if userid is MISSING:
            userid = await self.bot.db.fetchval(
                "SELECT spotify FROM users WHERE id=$1", inter.user.id
            )
            self.bot.spotify_users[inter.user.id] = userid

        if userid is None:
            return await inter.send_embed(
                "Unlinked",
                f"You don't have a Spotify account linked, please use `{inter.clean_prefix}spotify",
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
                return await inter.send_embed(
                    "Error", "Something went wrong, could not find your playlists"
                )

            count += len(playlists["items"])
            all_playlists += playlists["items"]
            total = playlists["total"]

        if not len(all_playlists):
            return await inter.send_embed(
                "No playlists",
                "**You do not have any public playlists!** \nPlease refer this to make your playlist public- https://www.androidauthority.com/make-spotify-playlist-public-3075538/",
            )

        view = PlaylistView(all_playlists)

        m = await inter.send("Choose a public playlist", view=view)
        if (not m and isinstance(inter, BBMyInter)) or (
            isinstance(m, PartialInteractionMessage) and isinstance(inter, BBMyInter)
        ):
            m = await inter.original_message()

        assert m is not None

        view.message = m

        await view.wait()

        if view.uri is None:
            for child in view.children:
                if isinstance(child, (Button, Select)):
                    child.disabled = True

            return await view.message.edit(content="You took too long...", view=view)

        await self.play(inter, query=view.uri)

    @connected()
    @slash_command(dm_permission=False)
    async def grab(self, inter: MyInter):
        """Sends the current playing song through direct messages"""

        if not inter.guild.voice_client.is_playing:
            return await inter.send_author_embed("No song is playing")

        await inter.send("📬 Grabbed", ephemeral=True)
        return await playing_embed(
            inter.guild.voice_client.current, save=True, override_inter=inter
        )

    @connected()
    @slash_command(dm_permission=False)
    async def forward(self, inter: MyInter, num: int):
        """Seeks forward in the current song by an amount"""

        player = inter.guild.voice_client
        c = player.position
        amount = c + (num * 1000)
        current = strftime("%H:%M:%S", gmtime((amount // 1000)))
        await player.seek(amount)
        await inter.send_author_embed(f"Position seeked to {current}")

    @connected()
    @slash_command(dm_permission=False)
    async def remove(self, inter: MyInter, num: int):
        """Remove a selected song from the queue."""

        player = inter.guild.voice_client
        try:
            song_n = player.queue[num - 1]
            player.queue.pop(num - 1)
        except IndexError:
            return await inter.send(
                "Please input a number which is within your queue!", ephemeral=True
            )

        await inter.send_author_embed(f"{song_n} removed from queue")

    @connected()
    @slash_command(name="clear-queue", dm_permission=False)
    async def clear_queue(self, inter: MyInter):
        """Clear the queue keeping the current song playing."""

        player = inter.guild.voice_client
        if not player.queue:
            await inter.send_author_embed("Queue is empty")
        else:
            player.queue.clear()
            await inter.send_author_embed("Cleared the queue")

    @slash_command(name="playnow",dm_permission=False)
    async def play_now(self,inter:MyInter,*,query:str):
        """Play the song immediately"""
        assert (
            isinstance(inter.user, Member)
            and inter.user.voice is not None
            and inter.user.voice.channel is not None
        )

        if not inter.guild.voice_client:
            await self.join(inter)

        await inter.send(f"Searching `{query}`")

        player = inter.guild.voice_client
        result = await player.get_tracks(query=query, ctx=inter)  # type: ignore

        if not result:
            return await inter.send_author_embed("No tracks found")

        result = result[0]
        player.queue.insert(0,result)
        toplay = inter.guild.voice_client.queue.pop(0)
        await inter.guild.voice_client.play(toplay)
        await playing_embed(result)


    @slash_command(dm_permission=False)
    async def bassboost(self,inter:MyInter):
        player = inter.guild.voice_client
        if not player.has_filter('boost'):
            await player.add_filter(Equalizer.boost('boost'))
            await inter.send("added")
        else:
            await inter.send("nope")
        #Logger.info(player.get_filters())
        



def setup(bot: Vibr):
    bot.add_cog(Music(bot))
