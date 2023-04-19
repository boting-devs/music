from asyncio import Event, gather, new_event_loop, set_event_loop
from signal import SIGINT, SIGTERM

import uvloop

from .manager import Manager


async def start(*, manager: Manager, event: Event) -> None:
    await gather(event.wait(), manager.start())


def main() -> None:
    event = Event()
    loop = new_event_loop()
    loop.add_signal_handler(SIGINT, event.set)
    loop.add_signal_handler(SIGTERM, event.set)
    set_event_loop(loop)
    uvloop.install()
    manager = Manager(event=event, loop=loop)

    try:
        loop.run_until_complete(start(manager=manager, event=event))
    finally:
        loop.run_until_complete(manager.close())
        loop.close()
