from __future__ import annotations

import datetime  # noqa: F401  # wtf
from logging import getLogger
from typing import TYPE_CHECKING, TypedDict, cast

import botbase
import nextcord
import pomice
from nextcord import Embed
from nextcord.abc import Messageable
from pomice import Track

if TYPE_CHECKING:
    from vibr.__main__ import Vibr
    from asyncio import TimerHandle

log = getLogger(__name__)


class Player(pomice.Player):
    PAUSE_TIMEOUT = 30
    DISCONNECT_TIMEOUT = 60 * 10

    # PAUSE_TIMEOUT = 10
    # DISCONNECT_TIMEOUT = 20

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.queue: list[pomice.Track] = []
        self.looped_track: pomice.Track | None = None
        self.looped_queue_check: bool = False
        self.loop_queue: list[pomice.Track] = []

        self.notification_channel: Messageable | None = None

        self._pause_timer: TimerHandle | None = None
        self._disconnect_timer: TimerHandle | None = None

    async def play(
        self,
        track: Track,
        *,
        start: int = 0,
        end: int = 0,
        ignore_if_playing: bool = False,
    ) -> Track:
        self.cancel_pause_timer()

        return await super().play(
            track, start=start, end=end, ignore_if_playing=ignore_if_playing
        )

    async def set_pause(self, pause: bool) -> bool:
        if pause:
            self.start_disconnect_timer()
        else:
            self.cancel_disconnect_timer()

        return await super().set_pause(pause)

    async def stop(self):
        self.start_disconnect_timer()

        return await super().stop()

    def cancel_pause_timer(self) -> None:
        if self._pause_timer:
            self._pause_timer.cancel()
            self._pause_timer = None

    def cancel_disconnect_timer(self) -> None:
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

    async def _pause_task(self) -> None:
        await self.set_pause(True)
        self._pause_timer = None

        if channel := self.notification_channel:
            embed = Embed(
                title="Pausing Due to No Listeners",
                description=(
                    "To prevent unnecessary resource usage, "
                    "I have paused the player."
                ),
                color=cast("Vibr", self.bot).color,
            )
            await channel.send(embed=embed)

    async def _disconnect_task(self) -> None:
        await self.destroy()
        self._disconnect_timer = None

        if channel := self.notification_channel:
            embed = Embed(
                title="Disconnecting Due to No Activity",
                description=(
                    "To prevent unnecessary resource usage, "
                    "I have disconnected the player."
                ),
                color=cast("Vibr", self.bot).color,
            )
            await channel.send(embed=embed)

    def start_pause_timer(self) -> None:
        if self.is_paused or not self.current:
            return

        self._pause_timer = self.client.loop.call_later(
            self.PAUSE_TIMEOUT, lambda: self.client.loop.create_task(self._pause_task())
        )

    def start_disconnect_timer(self) -> None:
        self._disconnect_timer = self.client.loop.call_later(
            self.DISCONNECT_TIMEOUT,
            lambda: self.client.loop.create_task(self._disconnect_task()),
        )


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
