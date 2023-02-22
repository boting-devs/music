from __future__ import annotations

from asyncio import gather
from os import environ
from typing import TYPE_CHECKING

import orjson
from botbase import BotBase
from mafic import Group, NodePool, Region, VoiceRegion
from nextcord import Intents

if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import NotRequired

    class LavalinkInfo(TypedDict):
        host: str
        port: int
        password: str
        regions: NotRequired[list[str]]
        label: str


__all__ = ("Vibr", "GUILD_IDS")


REGION_CLS = [Group, Region, VoiceRegion]
GUILD_IDS = [939509053623795732, 802586580766162964]


class Vibr(BotBase):
    def __init__(self):
        super().__init__(
            version="3.0.0",
            colours=[0xFF00E1, 0xDA00FF, 0x8000FF, 0x2500FF, 0x008FFF],
            name="vibr",
            log_channel=939853360289419284,
            guild_ids=GUILD_IDS,
            log_guilds=True,
            intents=Intents(guilds=True, voice_states=True),
        )

        self.pool = NodePool(self)

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

    async def add_nodes(self) -> None:
        with open(environ["LAVALINK_FILE"], "rb") as f:
            data: list[LavalinkInfo] = orjson.loads(f.read())

        for node in data:
            regions: list[Group | Region | VoiceRegion] | None = None
            if "regions" in node:
                regions = []
                for region_str in node["regions"]:
                    for cls in REGION_CLS:
                        if region_str in cls.__members__.keys():
                            region = cls[region_str]
                            break
                    else:
                        raise ValueError(f"Invalid region: {region_str}")

                    regions.append(region)

            await self.pool.create_node(
                host=node["host"],
                port=node["port"],
                password=node["password"],
                regions=regions,
                label=node["label"],
            )

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await gather(self.add_nodes(), super().start(token, reconnect=reconnect))
