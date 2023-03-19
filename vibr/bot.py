from __future__ import annotations

from asyncio import gather
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from botbase import BotBase, MyInter
from mafic import Group, NodePool, Region, VoiceRegion
from nextcord import ApplicationCommandType, Intents, SlashApplicationCommand

from vibr.constants import COLOURS, GUILD_IDS
from vibr.embed import ErrorEmbed

if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import NotRequired

    class LavalinkInfo(TypedDict):
        host: str
        port: int
        password: str
        regions: NotRequired[list[str]]
        label: str


__all__ = ("Vibr",)


REGION_CLS = [Group, Region, VoiceRegion]


class Vibr(BotBase):
    def __init__(self) -> None:
        super().__init__(
            version="3.0.0",
            colours=COLOURS,
            name="vibr",
            log_channel=939853360289419284,
            guild_ids=GUILD_IDS,
            log_guilds=True,
            intents=Intents(guilds=True, voice_states=True),
        )

        self.pool = NodePool(self)

    async def launch_shard(
        self, _gateway: str, shard_id: int, *, initial: bool = False
    ) -> None:
        return await super().launch_shard(
            environ["GW_PROXY"], shard_id, initial=initial
        )

    async def before_identify_hook(
        self, _shard_id: int | None, *, initial: bool = False  # noqa: ARG002
    ) -> None:
        # gateway-proxy
        return

    async def add_nodes(self) -> None:
        with Path(environ["LAVALINK_FILE"]).open("rb") as f:
            data: list[LavalinkInfo] = yaml.safe_load(f)  # pyright: ignore

        for node in data:
            regions: list[Group | Region | VoiceRegion] | None = None
            if "regions" in node:
                regions = []
                for region_str in node["regions"]:
                    for cls in REGION_CLS:
                        if region_str in cls.__members__:
                            region = cls[region_str]
                            break
                    else:
                        msg = f"Invalid region: {region_str}"
                        raise ValueError(msg)

                    regions.append(region)

            passwd = node["password"]

            await self.pool.create_node(
                host=node["host"],
                port=node["port"],
                password=environ[
                    passwd.removeprefix("$") if passwd.startswith("$") else passwd
                ],
                regions=regions,
                label=node["label"],
            )

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await gather(self.add_nodes(), super().start(token, reconnect=reconnect))

    async def process_application_commands(self, inter: MyInter) -> None:
        permissions = inter.app_permissions

        if not permissions.view_channel:
            embed = ErrorEmbed(
                title="I Am Missing Permissions",
                description="I am missing the `View Channel` permission "
                "in the channel you are sending the command in.",
            )
            await inter.response.send_message(
                embed=embed, view=embed.view, ephemeral=True
            )
            return

        if not permissions.send_messages:
            embed = ErrorEmbed(
                title="I Am Missing Permissions",
                description="I am missing the `Send Messages` permission "
                "in the channel you are sending the command in.",
            )
            await inter.response.send_message(
                embed=embed, view=embed.view, ephemeral=True
            )
            return

        if not permissions.embed_links:
            embed = ErrorEmbed(
                title="I Am Missing Permissions",
                description="I am missing the `Embed Links` permission "
                "in the channel you are sending the command in.",
            )
            await inter.response.send_message(
                embed=embed, view=embed.view, ephemeral=True
            )
            return

        await super().process_application_commands(inter)

    def get_command_mention(self, name: str) -> str:
        command = self.get_application_command_from_signature(
            name=name, cmd_type=ApplicationCommandType.chat_input.value, guild_id=None
        )
        assert isinstance(command, SlashApplicationCommand)

        return command.get_mention(guild=None) if command else f"/{name}"
