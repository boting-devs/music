from __future__ import annotations

import asyncio
from asyncio import gather, sleep
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from async_spotify import SpotifyApiClient
from async_spotify.authentification.authorization_flows import ClientCredentialsFlow
from botbase import BotBase
from mafic import Group, NodePool, Playlist, Region, SearchType, Track, VoiceRegion
from nextcord import (
    ApplicationCommandType,
    Intents,
    Member,
    MemberCacheFlags,
    SlashApplicationCommand,
    StageChannel,
    VoiceChannel,
)

from vibr.constants import COLOURS, GUILD_IDS
from vibr.db.player import PlayerConfig
from vibr.embed import Embed, ErrorEmbed
from vibr.sharding import TOTAL_SHARDS, shard_ids
from vibr.track_embed import track_embed

from . import errors
from .player import Player

if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import NotRequired

    from vibr.buttons import PlayButtons

    from .inter import Inter

    class LavalinkInfo(TypedDict):
        host: str
        port: int
        password: str
        regions: NotRequired[list[str]]
        label: str


__all__ = ("Vibr",)


REGION_CLS = [Group, Region, VoiceRegion]
DEFAULT_VOLUME = 100
LOG_CHANNEL = int(environ["LOG_CHANNEL"])


class Vibr(BotBase):
    def __init__(self) -> None:
        super().__init__(
            version="3.0.0",
            colours=COLOURS,
            name="vibr",
            log_channel=LOG_CHANNEL,
            guild_ids=GUILD_IDS,
            log_guilds=True,
            intents=Intents(guilds=True, voice_states=True),
            member_cache_flags=MemberCacheFlags.none(),
            shard_count=TOTAL_SHARDS,
            shard_ids=shard_ids,
        )

        self.pool = NodePool(self)

        auth = ClientCredentialsFlow(
            application_id=environ["SPOTIFY_CLIENT_ID"],
            application_secret=environ["SPOTIFY_CLIENT_SECRET"],
        )
        self.spotify = SpotifyApiClient(auth, hold_authentication=True)

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
                host=node["host"].replace("host", environ["HOST_IP"]),
                port=node["port"],
                password=environ[
                    passwd.removeprefix("$") if passwd.startswith("$") else passwd
                ],
                regions=regions,
                label=node["label"],
            )

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.spotify.create_new_client()
        await self.spotify.get_auth_token_with_client_credentials()

        await gather(self.add_nodes(), super().start(token, reconnect=reconnect))

    async def process_application_commands(self, inter: Inter) -> None:
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
        commands = name.split(" ")
        command = self.get_application_command_from_signature(
            name=commands.pop(0),
            cmd_type=ApplicationCommandType.chat_input.value,
            guild_id=None,
        )

        assert isinstance(command, SlashApplicationCommand | None)

        if commands and command:
            subcommand = command.children.get(commands.pop(0))

            if subcommand:
                command = subcommand
            else:
                return f"`/{name}`"

        if commands and command:
            subcommand = command.children.get(commands.pop(0))

            if subcommand:
                command = subcommand
            else:
                return f"`/{name}`"

        if command:
            return command.get_mention(None)

        return f"`/{name}`"

    async def set_player_settings(self, player: Player, channel_id: int) -> None:
        config = (
            await PlayerConfig.select(PlayerConfig.volume)
            .where(PlayerConfig.channel_id == channel_id)
            .first()
        )
        if config is None:
            return

        if config["volume"] == DEFAULT_VOLUME:
            return

        # TODO: Add actual public interface to mafic.
        for _ in range(3):
            if player.connected and player._node is not None:
                break

            await sleep(1)

        await player.set_volume(config["volume"])

    async def play(
        self,
        inter: Inter,
        query: str,
        search_type: str = SearchType.YOUTUBE.value,
        type: str | None = None,
    ) -> None:
        await self.assert_player(inter=inter)
        player = inter.guild.voice_client
        player.notification_channel = inter.channel  # pyright: ignore

        result = await player.fetch_tracks(
            query=query, search_type=SearchType(search_type)
        )
        if not result:
            raise errors.NoTracksFound

        if isinstance(result, Playlist):
            tracks = result.tracks
            item = result
            track = tracks[0]
        else:
            item = track = result[0]
            tracks = [track]

        if player.current is None:
            queued = tracks[1:]
            await player.play(track)

            embed, view = await track_embed(item, bot=self, user=inter.user.id)

            if queued:
                if type == "Next":
                    for i in tracks[::-1]:
                        player.queue.insert(0, i, inter.user.id)
                else:
                    player.queue += [(track, inter.user.id) for track in queued]
        elif type == "Next":
            embed, view = await self.handle_play_next(
                player=player, inter=inter, item=item, tracks=tracks
            )
        elif type == "Now":
            embed, view = await self.handle_play_now(
                player=player, inter=inter, item=item, tracks=tracks
            )
        else:
            player.queue += [(track, inter.user.id) for track in tracks]
            length = len(player.queue)
            embed, view = await track_embed(
                item, bot=self, user=inter.user.id, queued=length
            )

        await inter.send(embed=embed, view=view)  # pyright: ignore

    async def handle_play_now(
        self,
        *,
        player: Player,
        inter: Inter,
        item: Track | Playlist,
        tracks: list[Track],
    ) -> tuple[Embed, PlayButtons]:
        for i in tracks[::-1]:
            player.queue.insert(0, i, inter.user.id)
        track, user = player.queue.skip(1)
        embed, view = await track_embed(item, bot=self, user=user)
        await player.play(track)

        return embed, view

    async def handle_play_next(
        self,
        *,
        player: Player,
        inter: Inter,
        item: Track | Playlist,
        tracks: list[Track],
    ) -> tuple[Embed, PlayButtons]:
        for i in tracks[::-1]:
            player.queue.insert(0, i, inter.user.id)
        embed, view = await track_embed(item, bot=self, user=inter.user.id, queued=1)
        return embed, view

    async def assert_player(self, *, inter: Inter) -> None:
        if not inter.guild.voice_client:
            await self.join(inter=inter, channel=None)

    async def join(
        self, *, inter: Inter, channel: StageChannel | VoiceChannel | None
    ) -> None:
        if channel is None:
            channel = inter.user.voice and inter.user.voice.channel

            if channel is None:
                raise errors.UserNotInVoice

        if not await self.can_connect(channel, inter=inter):
            return

        try:
            player = await channel.connect(cls=Player, timeout=2)
        except asyncio.TimeoutError as e:
            raise errors.VoiceConnectionError from e

        await self.set_player_settings(player, channel.id)

        embed = Embed(
            title="Connected!", description=f"Connected to {channel.mention}."
        )

        await inter.send(embed=embed)  # pyright: ignore

    async def can_connect(
        self, channel: VoiceChannel | StageChannel, *, inter: Inter
    ) -> bool:
        assert isinstance(inter.me, Member)

        if not channel.permissions_for(inter.me).connect:
            embed = ErrorEmbed(
                title="I Cannot Connect",
                description=(
                    f"I do not have permission to connect to {channel.mention}."
                ),
            )
            await inter.send(embed=embed, view=embed.view, ephemeral=True)
            return False

        if channel.user_limit and len(channel.voice_states) >= channel.user_limit:
            permissions = channel.permissions_for(channel.guild.me)
            if not (permissions.move_members or permissions.administrator):
                embed = ErrorEmbed(
                    title="I Cannot Connect",
                    description=f"{channel.mention} is full, "
                    "and I do not have permission to move members.",
                )
                await inter.send(embed=embed, view=embed.view, ephemeral=True)
                return False

        return True
