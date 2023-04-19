from __future__ import annotations

from os import environ
from typing import TYPE_CHECKING

from redis.asyncio import from_url

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Event


class Manager:
    def __init__(self, *, event: Event, loop: AbstractEventLoop) -> None:
        self.event = event
        self.loop = loop
        self.redis = from_url(environ["REDIS_URL"])
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)

    async def start(self) -> None:
        self.loop.create_task(self.handle_messages())

    async def close(self) -> None:
        self.event.set()
        await self.redis.close()

    async def handle_messages(self) -> None:
        async for message in self.pubsub.listen():
            print(message)
