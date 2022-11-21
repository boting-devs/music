from __future__ import annotations

import datetime  # noqa: F401  # wtf
from asyncio import create_task
from logging import getLogger
from typing import TYPE_CHECKING, TypedDict

import botbase
import nextcord
import pomice

if TYPE_CHECKING:
    from asyncio import TimerHandle

    from pomice import Track

log = getLogger(__name__)

LEAVE_TIMEOUT = 5 * 60
"""The time to wait until auto-leaving the vc."""

PAUSE_TIMEOUT = 30
"""The time to wait before auto-pausing the player."""


class Player(pomice.Player):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.queue: list[pomice.Track] = []
        self.looped_track: pomice.Track | None = None
        self.looped_queue_check: bool = False
        self.loop_queue: list[pomice.Track] = []
        self.leave_timer: TimerHandle | None = None
        """This is the object returned by call_later that lets us cancel autoleave."""

        self.pause_timer: TimerHandle | None = None
        """This is the object returned by call_later that lets us cancel autopause."""

    def invoke_leave_timer(self, track: Track) -> None:
        """This is called when the player should auto-leave."""

        inter: MyInter = track.ctx  # type: ignore

        if self.leave_timer is not None:
            self.leave_timer.cancel()

        log.info("Invoking leave timer for %d", inter.guild.id)
        self.leave_timer = self.client.loop.call_later(
            LEAVE_TIMEOUT, lambda: create_task(self.leave(inter))
        )

    def cancel_leave_timer(self) -> None:
        """This is called when the player should not auto-leave."""

        if self.leave_timer is not None:
            log.info("Cancelling leave timer for %d", self.current.ctx.guild.id)  # type: ignore
            self.leave_timer.cancel()
            self.leave_timer = None

    def invoke_pause_timer(self) -> None:
        """This is called when the player should auto-pause."""

        inter: MyInter = self.current.ctx  # type: ignore

        if self.pause_timer is not None:
            self.pause_timer.cancel()

        log.info("Invoking pause timer for %d", inter.guild.id)
        self.pause_timer = self.client.loop.call_later(
            PAUSE_TIMEOUT, lambda: create_task(self.autopause(inter))
        )

    def cancel_pause_timer(self) -> None:
        """This is called when the player should not auto-pause."""

        if self.pause_timer is not None:
            log.info("Cancelling pause timer for %d", self.current.ctx.guild.id)  # type: ignore
            self.pause_timer.cancel()
            self.pause_timer = None

    def track_end(self, track: Track) -> None:
        """Called when a track ends and nothing is in the queue.

        Track is given to use the last known interaction.
        """

        self.invoke_leave_timer(track)

    async def play(
        self,
        track: Track,
        *,
        start: int = 0,
        end: int = 0,
        ignore_if_playing: bool = False,
    ) -> Track:
        ret = await super().play(
            track, start=start, end=end, ignore_if_playing=ignore_if_playing
        )

        self.cancel_leave_timer()

        return ret

    async def leave(self, inter: MyInter) -> None:
        """This is called when autoleave should be invoked."""

        await inter.send_embed(
            "Disconnecting Due to No Activity",
            "To prevent unnecessary resource usage, I have disconnected the player.",
        )

        log.info("Auto-destroying player for %d", inter.guild.id)
        await self.destroy()

    async def autopause(self, inter: MyInter) -> None:
        """This is called when autopause should be invoked."""

        await inter.send_embed(
            "Pausing Due to No Listeners",
            "To prevent unnecessary resource usage, I have paused the player.",
        )

        log.info("Auto-pausing player for %d", inter.guild.id)
        await self.set_pause(True)

    async def set_pause(self, pause: bool) -> bool:
        ret = await super().set_pause(pause)

        if ret:
            self.invoke_leave_timer(self.current)
        else:
            self.cancel_leave_timer()

        return ret


class MyContext(botbase.MyContext):
    voice_client: Player
    guild: FakeGuild


class FakeGuild(nextcord.Guild):
    voice_client: Player


class MyInter(botbase.MyInter):
    guild: FakeGuild
    voice_client: Player

    # Pomice fuckery.
    @property
    def author(self):
        return self.user


class SpotifyPlaylists(TypedDict):
    href: str
    items: list[Playlist]
    limit: int
    next: str | None
    offset: int
    previous: str | None
    total: int


class Playlist(TypedDict):
    url: str
    type: str
    tracks: list[SpotifyTrack]
    snapshot_id: str
    public: bool
    owner: SpotifyUser
    name: str
    images: list[Image]
    id: str
    href: str
    followers: Followers
    external_urls: ExtUrl
    description: str | None
    collaborative: bool


class Image(TypedDict):
    width: int
    height: int
    url: str


class SpotifyTrack(TypedDict):
    total: int
    previous: str | None
    offset: str
    next: str | None
    limit: int
    items: list[dict]
    href: str


class SpotifyUser(TypedDict):
    display_name: str
    uri: str
    type: str
    id: str
    href: str
    followers: Followers


class Followers(TypedDict):
    href: str
    total: int
    external_urls: ExtUrl


class ExtUrl(TypedDict):
    spotify: str


class NotificationDict(TypedDict):
    id: int
    title: str
    notification: str
    datetime: datetime.datetime


class Notification:
    def __init__(self, data: NotificationDict) -> None:
        self.id = data["id"]
        self.title = data["title"]
        self.message = data["notification"]
        self.time = data["datetime"]

    def format(self) -> str:
        return f"{self.id}. **{self.title}**\n{self.message}"
