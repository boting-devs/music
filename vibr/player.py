from __future__ import annotations

import random
from collections import deque
from typing import TYPE_CHECKING

from mafic import Player as MaficPlayer
from mafic.track import Track

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mafic import Node, Track
    from mafic.type_variables import ClientT
    from nextcord.abc import Connectable, Messageable

__all__ = ("Player", "Queue")
MAX_QUEUE_LENGTH = 500


class Queue:
    def __init__(self, maxlen: int) -> None:
        # This does not use `maxlen` in deque, since then you lose the first item
        # when appending.
        self._stack: deque[tuple[Track, int]] = deque()
        self._maxlen = maxlen

    def extend(self, items: Sequence[tuple[Track, int]]) -> None:
        if (len(self._stack) + len(items)) == self._maxlen:
            raise IndexError

        self._stack.extend(items)

    def add(self, track: Track, user: int) -> None:
        self._stack.append((track, user))

    def __iadd__(self, other: Sequence[tuple[Track, int]]) -> Queue:
        self.extend(other)
        return self

    def __len__(self) -> int:
        return len(self._stack)

    def take(self) -> tuple[Track, int]:
        return self._stack.popleft()

    def skip(self, amount: int) -> tuple[Track, int]:
        track = None

        for _ in range(amount):
            track = self.take()

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
        self._stack.insert(index, (track, user))

    def index(self, track: Track) -> None:
        return self._stack.index(track)


class Player(MaficPlayer):
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

        return await super().play(
            track,
            start_time=start_time,
            end_time=end_time,
            volume=volume,
            replace=replace,
            pause=pause,
        )
