from __future__ import annotations

import random
from collections import deque
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

import mafic
from mafic import Track

from vibr.embed import Embed
from vibr.errors import QueueFull

if TYPE_CHECKING:
    from asyncio import TimerHandle
    from collections.abc import Coroutine, Sequence

    from mafic import Node
    from mafic.type_variables import ClientT
    from nextcord.abc import Connectable, Messageable

__all__ = ("Player", "Queue")
MAX_QUEUE_LENGTH = 500


class LoopType(Enum):
    QUEUE = auto()
    TRACK = auto()


class Queue:
    def __init__(self, maxlen: int) -> None:
        # This does not use `maxlen` in deque, since then you lose the first item
        # when appending.
        self._stack: deque[tuple[Track, int]] = deque()
        self._maxlen = maxlen
        self._loop_type: LoopType | None = None
        self._loop_type_queue: LoopType | None = None

    @property
    def loop_type(self) -> LoopType | None:
        return self._loop_type
    

    def loop_track(self, track: Track, *, user: int) -> None:
        if self._loop_type == LoopType.TRACK:
            return
        else:
            self._loop_type = LoopType.TRACK
            self._stack.appendleft((track, user))

    def loop_track_once(self, track: Track, *, user: int) -> None:
        if self._loop_type == LoopType.TRACK:
            self._stack.popleft()
        self._stack.appendleft((track, user))
        self._loop_type = None
        
    def loop_queue(self, *, current: Track, user: int) -> None:
        self._loop_type_queue = LoopType.QUEUE
        self._stack.append((current, user))


    def disable_loop(self) -> None:
        self._stack.popleft()
        self._loop_type = None

    def disable_loop_queue(self) -> None:
        self._loop_type_queue = None

    def extend(self, items: Sequence[tuple[Track, int]]) -> None:
        if (len(self._stack) + len(items)) > self._maxlen:
            items = items[: self._maxlen - len(self._stack)]

            if not items:
                raise QueueFull

        self._stack.extend(items)

    def add(self, track: Track, user: int) -> None:
        if len(self._stack) == self._maxlen:
            raise QueueFull

        self._stack.append((track, user))

    def __iadd__(self, other: Sequence[tuple[Track, int]]) -> Queue:
        self.extend(other)
        return self

    def __len__(self) -> int:
        return len(self._stack)

    def take(self, skip: bool = False) -> tuple[Track, int]:
        if self._loop_type_queue == LoopType.QUEUE:
            item = self._stack.popleft()
            self._stack.append(item)
            return item

        if self._loop_type == LoopType.TRACK and not skip:
            return self._stack[0]

        return self._stack.popleft()

    def skip(self, amount: int) -> tuple[Track, int]:
        track = None

        for _ in range(amount):
            track = self.take(skip=True)

        assert track is not None

        return track

    @property
    def tracks(self) -> list[Track]:
        return [track for track, _ in self._stack]

    def clear(self) -> None:
        self._stack.clear()

    def __getitem__(self, index: int) -> Track:
        return self._stack[index][0]

    def shuffle(self) -> None:
        random.shuffle(self._stack)

    def pop(self, index: int) -> None:
        del self._stack[index]

    def insert(self, index: int, track: Track, user: int) -> None:
        if len(self._stack) == self._maxlen:
            raise QueueFull

        self._stack.insert(index, (track, user))

    def index(self,query:Track) -> int | None:
        index = next((index for index, (track, _) in enumerate(self._stack) if track == query), None)
        return index

class Player(mafic.Player):
    PAUSE_TIMEOUT = 30
    DISCONNECT_TIMEOUT = 60 * 10

    def __init__(
        self,
        client: ClientT,
        channel: Connectable,
        *,
        node: Node[ClientT] | None = None,
    ) -> None:
        super().__init__(client, channel, node=node)

        self.queue: Queue = Queue(maxlen=MAX_QUEUE_LENGTH)
        self.notification_channel: Messageable | None = None

        self.loop_track: Track | None = None
        self.looped_user: int
        self.loop_queue: list[Track] = []
        self.loop_queue_check: bool = False
        self.dnd: bool = False

        self._pause_timer: TimerHandle | None = None
        self._disconnect_timer: TimerHandle | None = None

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_mute: bool = False,
        self_deaf: bool = False,  # noqa: ARG002
    ) -> None:
        ret = await super().connect(
            timeout=timeout,
            reconnect=reconnect,
            self_mute=self_mute,
            self_deaf=True,
        )
        self.start_disconnect_timer()
        return ret

    async def play(
        self,
        track: Track | str,
        /,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        volume: int | None = None,
        replace: bool = True,
        pause: bool | None = None,
    ) -> None:
        # Handle `/spotify playlists`` not having a lavalink ID.
        if isinstance(track, Track) and not track.id:
            assert track.uri is not None
            track = track.uri

        if track is not None:
            self.cancel_pause_timer()
            self.cancel_disconnect_timer()

        return await super().play(
            track,
            start_time=start_time,
            end_time=end_time,
            volume=volume,
            replace=replace,
            pause=pause,
        )

    async def pause(self, pause: bool = True) -> None:
        if pause:
            self.start_disconnect_timer()
        else:
            self.cancel_disconnect_timer()

        return await super().pause(pause)

    def stop(self) -> Coroutine[Any, Any, None]:
        self.start_disconnect_timer()

        return super().stop()

    def destroy(self) -> Coroutine[Any, Any, None]:
        self.cancel_pause_timer()
        self.cancel_disconnect_timer()

        return super().destroy()

    def cancel_pause_timer(self) -> None:
        if self._pause_timer:
            self._pause_timer.cancel()
            self._pause_timer = None

    def cancel_disconnect_timer(self) -> None:
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

    async def _pause_task(self) -> None:
        await self.pause()
        self._pause_timer = None

        if channel := self.notification_channel:
            embed = Embed(
                title="Pausing Due to No Listeners",
                description=(
                    "To prevent unnecessary resource usage, "
                    "I have paused the player."
                ),
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
            )
            await channel.send(embed=embed)

    def start_pause_timer(self) -> None:
        if self.paused or not self.current:
            return

        if self._pause_timer is not None:
            return

        self._pause_timer = self.client.loop.call_later(
            self.PAUSE_TIMEOUT, lambda: self.client.loop.create_task(self._pause_task())
        )

    def start_disconnect_timer(self) -> None:
        if self._disconnect_timer is not None:
            return

        self._disconnect_timer = self.client.loop.call_later(
            self.DISCONNECT_TIMEOUT,
            lambda: self.client.loop.create_task(self._disconnect_task()),
        )
