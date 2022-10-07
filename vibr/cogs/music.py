from __future__ import annotations

from asyncio import sleep
from difflib import get_close_matches
from functools import partial
from logging import getLogger
from random import shuffle
from time import gmtime, strftime
from typing import TYPE_CHECKING, Optional, cast

from botbase import MyInter as BBMyInter
from bs4 import BeautifulSoup
from nextcord import (
    ClientUser,
    Embed,
    Member,
    PartialInteractionMessage,
    Range,
    User,
    slash_command,
)
from nextcord.ext.application_checks import (
    ApplicationBotMissingPermissions as BotMissingPermissions,
)
from nextcord.ext.commands import Cog
from nextcord.ui import Button, Select
from nextcord.utils import MISSING, utcnow, get
from pomice import Equalizer, Playlist, Rotation, Timescale, TrackLoadError

from .extras.checks import connected, connected_and_playing, voted
from .extras.errors import (
    Ignore,
    LyricsNotFound,
    NotConnected,
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
        elif not inter.app_permissions.send_messages:
            raise BotMissingPermissions(["send_messages"])
        elif not inter.app_permissions.view_channel:
            raise BotMissingPermissions(["view_channel"])
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

            try:
                await player.play(toplay)
            except Exception as e:
                embed = Embed(
                    title="Error when playing queued track",
                    description=f"{e}\nAttempting to play next track...",
                )
                if toplay.ctx:
                    channel = (
                        toplay.ctx.channel
                    )  # pyright: ignore[reportOptionalMemberAccess]
                    await channel.send(embed=embed)

                await self.on_pomice_track_end(player, track, "")
            else:
                await playing_embed(toplay)
        else:
            if (
                player.channel.guild.id in self.bot.whitelisted_guilds
                and self.bot.whitelisted_guilds[player.channel.guild.id] > utcnow()
            ):
                return

            self.bot.loop.create_task(self.leave_check(track.ctx))  # type: ignore

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

    async def set_persistent_settings(self, player: Player, channel: int) -> None:
        volume = await self.bot.db.fetchval(
            "SELECT volume FROM players WHERE channel=$1",
            channel,
        )
        if volume is None:
            volume = 100

        await player.set_volume(volume)

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
                return await inter.send_author_embed("Already Connected!")

        player = await channel.connect(cls=Player)

        await inter.send_author_embed(f"Connected to {channel.name}")

        await self.set_persistent_settings(player, channel.id)

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
            and inter.application_command.name != "join"
        ):
            self.bot.activity_tasks.pop(inter.guild.id, None)

    @slash_command(dm_permission=False)
    async def play(self, inter: MyInter, *, query: str):
        """Play some tunes!

        query:
            The song to search, can be a link, a query, or a playlist.
        """

        assert (
            isinstance(inter.user, Member)
            and inter.user.voice is not None
            and inter.user.voice.channel is not None
        )

        await inter.send(f"Searching `{query}`")

        if not inter.guild.voice_client:
            await self.join(inter)

        player = inter.guild.voice_client
        result = await player.get_tracks(query=query, ctx=inter)  # type: ignore

        if not result:
            return await inter.send_author_embed("No tracks found")

        if len(player.queue) >= 500:
            raise TooManyTracks()

        if player is None:
            raise NotConnected()

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

    @connected_and_playing()
    @slash_command(dm_permission=False)
    async def pause(self, inter: MyInter):
        """Pause the tunes"""

        player = inter.guild.voice_client

        await player.set_pause(True)
        log.debug("Paused player for guild %d", inter.guild.id)

        await inter.send_author_embed("Paused")

    @connected()
    @slash_command(dm_permission=False)
    async def resume(self, inter: MyInter):
        """Continue the bangers!"""

        player = inter.guild.voice_client

        await player.set_pause(False)
        log.debug("Resumed player for guild %d", inter.guild.id)

        await inter.send_author_embed("Resumed")

    @connected()
    @slash_command(dm_permission=False)
    async def stop(self, inter: MyInter):
        """Stop, wait a minute..."""

        player = inter.guild.voice_client

        player.queue = []
        await player.stop()
        log.debug("Stopped player for guild %d", inter.guild.id)

        await inter.send_author_embed("Stopped")

    @connected()
    @slash_command(dm_permission=False)
    async def disconnect(self, inter: MyInter):
        """Bye bye :("""

        player = inter.guild.voice_client
        await player.destroy()
        log.debug("Destroyed player for guild %d", inter.guild.id)

        await inter.send_author_embed("Bye :(")

    @connected()
    @slash_command(dm_permission=False)
    async def volume(self, inter: MyInter, *, number: Range[1, 500]):
        """Turn up the beats

        number:
            The volume to set, between 1 and 500, measured in % of normal.
        """

        vol = cast(int, number)

        player = inter.guild.voice_client
        await player.set_volume(vol)
        log.debug("Set volume for guild %d to %d", inter.guild.id, vol)

        if vol == 100:
            await self.bot.db.execute(
                """DELETE FROM players WHERE channel=$1""",
                player.channel.id,
            )
            log.debug(
                "Removing player record for channel %d",
                player.channel.id,
            )
        else:
            await self.bot.db.execute(
                """INSERT INTO players (channel, volume)
                    VALUES ($1, $2)
                    ON CONFLICT (channel) DO UPDATE
                        SET volume = $2""",
                player.channel.id,
                vol,
            )
            log.debug(
                "Updating player record for channel %d to volume %d",
                player.channel.id,
                vol,
            )

        await inter.send_author_embed(f"Volume set to '{vol}%'")

    @slash_command(dm_permission=False)
    @voted()
    async def lyrics(self, inter: MyInter, *, query: str = ""):
        """Sing along to your favourite tunes!

        query:
            The song to search lyrics for, do not input if you want the current song.
        """

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
            lyric.get_text("\n") + "\n"
            for lyric in BeautifulSoup(txt, "html.parser").select(
                "div[class*=Lyrics__Container]"
            )
        ]

        lyrics = "".join(lyricsform).replace("[", "\n[").strip()

        lyrics = self.truncate(lyrics, length=4096)

        embed = Embed(title=title, description=lyrics, color=self.bot.color)
        embed.set_author(name=artist)
        embed.set_thumbnail(url=thumbnail)

        await a.edit(embed=embed)

    @connected()
    @slash_command(dm_permission=False)
    async def skip(self, inter: MyInter):
        """When the beat isn't hitting right"""

        player = inter.guild.voice_client
        if not player.queue:
            await player.stop()
            log.debug("Stopping due to no queue for guild %d", inter.guild.id)
            return await inter.send_author_embed("Nothing in queue. Stopping the music")

        toplay = player.queue.pop(0)
        await player.play(toplay)
        log.debug("Skipping song for guild %d to %s", inter.guild.id, toplay.title)
        await playing_embed(toplay, skipped_by=inter.user.mention, override_inter=inter)

    @connected_and_playing()
    @slash_command(name="now-playing", dm_permission=False)
    async def now_playing(self, inter: MyInter):
        """Show the current beats."""

        return await playing_embed(
            inter.guild.voice_client.current,
            length=True,
            override_inter=inter,
        )

    @connected()
    @slash_command(dm_permission=False)
    async def shuffle(self, inter: MyInter):
        """Switch things up"""

        shuffle(inter.guild.voice_client.queue)
        log.debug("Shuffled queue for guild %d", inter.guild.id)

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

    @connected_and_playing()
    @slash_command(dm_permission=False)
    async def loop(self, inter: MyInter):
        """It hit so hard so you play it again"""

        player = inter.guild.voice_client

        current = player.current
        player.queue.insert(0, current)
        log.debug("Looped song %s for guild %d", current.title, inter.guild.id)

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
            spotify_cmd = get(self.bot.get_all_application_commands(), name="spotify")
            spotify_mention = spotify_cmd.get_mention() if spotify_cmd else "`/spotify`"
            return await inter.send_embed(
                "Unlinked",
                f"You don't have a Spotify account linked, please use {spotify_mention}.",
            )

        loop = self.bot.loop
        sp = self.bot.spotipy

        if sp is None:
            support = get(self.bot.get_all_application_commands(), name="support")
            support_mention = support.get_mention() if support else "`/support`"
            raise TrackLoadError(
                f"Spotify is unable to be used, please contact the developers at {support_mention}."
            )

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
                "**You do not have any public playlists!**\nPlease refer to this to make your playlist public- https://www.androidauthority.com/make-spotify-playlist-public-3075538/",
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

    @connected_and_playing()
    @slash_command(dm_permission=False)
    async def grab(self, inter: MyInter):
        """Sends the current playing song through direct messages"""

        await inter.send("📬 Grabbed", ephemeral=True)
        return await playing_embed(
            inter.guild.voice_client.current, save=True, override_inter=inter
        )

    @connected_and_playing()
    @slash_command(dm_permission=False)
    async def forward(self, inter: MyInter, num: int):
        """Seeks forward in the current song by an amount

        num:
            The amount to seek forward by in seconds.
        """

        player = inter.guild.voice_client
        c = player.position
        # s -> ms
        amount = c + (num * 1000)
        # Format the time into a human readable format.
        current = strftime("%H:%M:%S", gmtime((amount // 1000)))
        await player.seek(amount)
        await inter.send_author_embed(f"Position seeked to {current}")

    @slash_command(dm_permission=False)
    @connected()
    async def remove(self, inter: MyInter, num: int):
        """Remove a selected song from the queue.

        num:
            The number of the song to remove, found via the queue.
        """

        player = inter.guild.voice_client

        try:
            song_n = player.queue[num - 1]
            player.queue.pop(num - 1)
        except IndexError:
            return await inter.send(
                "Please input a number which is within your queue!", ephemeral=True
            )
        else:
            log.debug("Removed song %s for guild %d", song_n.title, inter.guild.id)

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
            log.debug("Cleared queue for guild %d", inter.guild.id)

    @slash_command(name="play-now", dm_permission=False)
    async def play_now(self, inter: MyInter, *, query: str):
        """Play the song immediately.

        query:
            The song to search, can be a link, a query, or a playlist.
        """
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

        # Either a playlist or a list of found tracks.
        result = result[0] if isinstance(result, list) else result.tracks[0]
        player.queue.insert(0, result)
        toplay = player.queue.pop(0)
        await player.play(toplay)
        await playing_embed(result)

    @connected_and_playing()
    @slash_command(name="bass-boost", dm_permission=False)
    async def bass_boost(self, inter: MyInter):
        """Increases bass of the song."""

        player = inter.guild.voice_client

        if player.filters.has_filter(filter_tag="boost"):
            await player.remove_filter(filter_tag="boost")
            await inter.send_author_embed("Bass Filter reset")
            log.debug("Bass Filter reset for guild %d", inter.guild.id)
        else:
            await player.add_filter(Equalizer.boost(), fast_apply=True)
            await inter.send_author_embed("Bassboost filter activated")
            log.debug("Bassboost filter activated for guild %d", inter.guild.id)

    @connected_and_playing()
    @slash_command(dm_permission=False)
    async def nightcore(self, inter: MyInter):
        """A funny filter. Just Try it out!"""

        player = inter.guild.voice_client

        if player.filters.has_filter(filter_tag="nightcore"):
            await player.remove_filter(filter_tag="nightcore")
            await inter.send_author_embed("Nightcore filter reset")
            log.debug("Nightcore filter reset for guild %d", inter.guild.id)
        else:
            await player.add_filter(Timescale.nightcore(), fast_apply=True)
            await inter.send_author_embed("Nightcore filter activated")
            log.debug("Nightcore filter activated for guild %d", inter.guild.id)

    @slash_command(dm_permission=False)
    @connected_and_playing()
    async def rotate(
        self,
        inter: MyInter,
        frequency: Optional[Range[0.1, 10]],
    ):
        """A cool filter to pan audio around your head,
        best with headphones or other stereo audio systems!

        frequency:
            The frequency in Hz (times/second) to pan audio.
            The best values are below 1, >5 is trippy."
        """

        passed_custom = frequency is not None
        # Default in slash is not used so we know if they did in fact input 0.2.
        frequency = frequency or 0.2  # Set default frequency.

        player = inter.guild.voice_client

        # Check if user passed a new frequency, it should not stop then.
        if player.filters.has_filter(filter_tag="rotation") and passed_custom:
            await player.remove_filter(filter_tag="rotation")
            await player.add_filter(
                Rotation(tag="rotation", rotation_hertz=frequency), fast_apply=True  # type: ignore
            )
            await inter.send_author_embed("Rotation filter modified")
            log.debug("Rotation filter modified for guild %d to %fhz", inter.guild.id)

        # If no custom frequency was passed, it should stop rotating.
        elif player.filters.has_filter(filter_tag="rotation"):
            await player.remove_filter(filter_tag="rotation")
            await inter.send_author_embed("Rotation filter reset")
            log.debug("Rotation filter reset for guild %d", inter.guild.id)

        # First time activating the filter.
        else:
            await player.add_filter(
                Rotation(tag="rotation", rotation_hertz=frequency), fast_apply=True  # type: ignore
            )
            await inter.send_author_embed("Rotation filter activated")
            log.debug("Rotation filter activated for guild %d", inter.guild.id)

    @slash_command(dm_permission=False)
    @connected()
    async def move(
        self, inter: MyInter, track: Range[1, ...], destination: Range[1, ...]
    ):
        """Move the song to a certain position in your queue.

        track:
            The number of the song to move, found via the queue.
        destination:
            The position to move the song to.
        """
        player = inter.guild.voice_client

        track_index = cast(int, track)
        dest_index = cast(int, destination)

        try:
            song = player.queue.pop(track_index - 1)
        except IndexError:
            return await inter.send(
                "Please input a number which is within your queue!", ephemeral=True
            )

        player.queue.insert(dest_index - 1, song)
        log.debug("Inserted %s at %d", song.title, dest_index - 1)
        dest_index = player.queue.index(song)
        await inter.send_author_embed(f"{song} position set to {dest_index}")

    @slash_command(name="play-next",dm_permission=False)
    @connected()
    async def playnext(self,inter:MyInter,*,track:Range[1, ...]=None,song:str=None):
        player = inter.guild.voice_client
        if track != None and song == None:
            track_index = cast(int, track)
            try:
                songplay = player.queue.pop(track_index - 1)
            except IndexError:
                return await inter.send(
                    "Please input a number which is within your queue!", ephemeral=True
                )
            player.queue.insert(0, songplay)
            await inter.send_author_embed(f"Playing the song - {songplay} up next!")
        
        elif track == None and song != None:
            result = await player.get_tracks(query=song, ctx=inter)
            player.queue.insert(0,result)

    @staticmethod
    def truncate(fmt: str, *, length: int) -> str:
        """Return the string with `...` if necessary."""

        if len(fmt) > length:
            return fmt[: length - 3] + "..."

        return fmt

    @remove.on_autocomplete("num")
    @move.on_autocomplete("track")
    async def on_move_num_autocomplete(self, inter: MyInter, num: Optional[int]):
        player = inter.guild.voice_client
        if player is None:
            return []

        queue = player.queue
        queue_size = len(queue)

        if num is None:
            # Send the top 25
            return {
                self.truncate(f"{i+1}. {t.title} - {t.author}", length=100): i + 1
                for i, t in enumerate(queue[:25])
            }
        else:
            # Get the 25 nearest to the number inputted.
            # We only get numbers from Discord as it is an `int` arg.
            matches = list(
                map(
                    int,
                    get_close_matches(str(num), map(str, range(1, queue_size)), n=25),
                )
            )
            tracks = [queue[i - 1] for i in matches]

            return {
                self.truncate(f"{i}. {t.title} - {t.author}", length=100): i
                for i, t in zip(matches, tracks)
            }


def setup(bot: Vibr):
    bot.add_cog(Music(bot))
