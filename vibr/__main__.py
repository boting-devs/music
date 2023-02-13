from __future__ import annotations

from os import environ

import uvloop
from botbase import BotBase
from nextcord import Intents


class Vibr(BotBase):
    async def launch_shard(
        self, gateway: str, shard_id: int, *, initial: bool = False
    ) -> None:
        return await super().launch_shard(
            environ["GW_PROXY"], shard_id, initial=initial
        )

    async def before_identify_hook(
        self, shard_id: int | None, *, initial: bool = False
    ) -> None:
        # gateway-proxy
        return

    async def on_application_command_error(self, inter, error):
        __import__("traceback").print_exception(type(error), error, error.__traceback__)


bot = Vibr(
    version="3.0.0",
    colours=[0xFF00E1, 0xDA00FF, 0x8000FF, 0x2500FF, 0x008FFF],
    name="vibr",
    log_channel=939853360289419284,
    guild_ids=[939509053623795732, 802586580766162964],
    log_guilds=True,
    intents=Intents(guilds=True, voice_states=True),
)


if __name__ == "__main__":
    uvloop.install()
    bot.run(environ["TOKEN"])
