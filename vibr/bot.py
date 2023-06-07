from __future__ import annotations

import asyncio
from asyncio import Event, gather, sleep
from logging import getLogger
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

import async_spotify
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
from nextcord.utils import utcnow
from redis import asyncio as redis

from vibr.constants import COLOURS, GUILD_IDS
from vibr.db import PlayerConfig
from vibr.db.node import Node
from vibr.embed import Embed, ErrorEmbed
from vibr.sharding import CURRENT_CLUSTER, TOTAL_SHARDS, shard_ids
from vibr.sharding import client as docker_client
from vibr.track_embed import track_embed
from vibr.utils import truncate

from . import errors
from .exts.playing._errors import LyricsNotFound, SongNotProvided
from .player import Player

if TYPE_CHECKING:
    from typing import TypedDict

    from async_spotify.authentification.spotify_authorization_token import (
        SpotifyAuthorisationToken,
    )
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

log = getLogger(__name__)
REGION_CLS = [Group, Region, VoiceRegion]
DEFAULT_VOLUME = 100
LOG_CHANNEL = int(environ["LOG_CHANNEL"])


class TokenRenewClass(async_spotify.TokenRenewClass):
    async def __call__(
        self, spotify_api_client: SpotifyApiClient
    ) -> SpotifyAuthorisationToken:
        return await spotify_api_client.get_auth_token_with_client_credentials()


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
        self.spotify = SpotifyApiClient(
            authorization_flow=auth,
            hold_authentication=True,
            token_renew_instance=TokenRenewClass(),
        )
        self.redis = redis.from_url(environ["REDIS_URL"])

        self.nodes_connected = Event()

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
            data: list[LavalinkInfo] = yaml.safe_load(
                f
            )  # pyright: ignore[reportGeneralTypeIssues]

        for node_data in data:
            regions: list[Group | Region | VoiceRegion] | None = None
            if "regions" in node_data:
                regions = []
                for region_str in node_data["regions"]:
                    for cls in REGION_CLS:
                        if region_str in cls.__members__:
                            region = cls[region_str]
                            break
                    else:
                        msg = f"Invalid region: {region_str}"
                        raise ValueError(msg)

                    regions.append(region)

            passwd = node_data["password"]

            resuming = (
                await Node.select(Node.session_id)
                .where(
                    (Node.label == node_data["label"])
                    & (Node.cluster == int(CURRENT_CLUSTER))
                )
                .first()
            )
            node = await self.pool.create_node(
                host=node_data["host"].replace("host", environ["HOST_IP"]),
                port=node_data["port"],
                password=environ[
                    passwd.removeprefix("$") if passwd.startswith("$") else passwd
                ],
                regions=regions,
                label=node_data["label"],
                resuming_session_id=resuming["session_id"] if resuming else None,
            )
            await Node.insert(
                Node(
                    {
                        Node.label: node.label,
                        Node.session_id: node.session_id,
                        Node.cluster: int(CURRENT_CLUSTER),
                    }
                )
            ).on_conflict(
                (Node.label, Node.session_id), "DO UPDATE", (Node.session_id,)
            )

        self.nodes_connected.set()

    async def listen_to_redis(self) -> None:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("bot")
        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue

            data = msg["data"]
            if data == b"shutdown":
                docker_client.update_container(
                    environ["HOSTNAME"], restart_policy={"Name": "no"}
                )
                await self.close()

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.spotify.create_new_client()
        await self.spotify.get_auth_token_with_client_credentials()

        await gather(
            self.add_nodes(),
            super().start(token, reconnect=reconnect),
            self.listen_to_redis(),
        )

    async def close(self) -> None:
        await self.redis.close()
        await self.pool.close()

        return await super().close()

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
        if player is None:
            return
        player.notification_channel = (
            inter.channel
        )  # pyright: ignore[reportGeneralTypeIssues]

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

            embed, view = await track_embed(item, user=inter.user.id)

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
            embed, view = await track_embed(item, user=inter.user.id, queued=length)

        m = await inter.send(
            embed=embed, view=view
        )  # pyright: ignore[reportGeneralTypeIssues]
        view.message = m

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
        embed, view = await track_embed(item, user=user)
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
        embed, view = await track_embed(item, user=inter.user.id, queued=1)
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
            log.debug("Connecting...", extra={"guild": inter.guild.id})
            player = await channel.connect(cls=Player, timeout=2)
        except asyncio.TimeoutError as e:
            raise errors.VoiceConnectionError from e

        log.debug("Setting player settings", extra={"guild": inter.guild.id})
        await self.set_player_settings(player, channel.id)

        embed = Embed(
            title="Connected!", description=f"Connected to {channel.mention}."
        )

        log.info("Player connected and set up", extra={"guild": inter.guild.id})
        await inter.send(embed=embed)  # pyright: ignore[reportGeneralTypeIssues]

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

    async def lyrics(self, inter: Inter, query: str | None = None) -> None:
        player: Player = inter.guild.voice_client
        if not query:
            if player is None or player.current is None:
                raise SongNotProvided

            assert player.current.title is not None
            if "-" in player.current.title:
                q = player.current.title
            else:
                q = player.current.title, player.current.author
        else:
            q = query

        await inter.response.defer()

        url_search = f"https://api.flowery.pw/v1/lyrics/search?query={q}"

        async with inter.client.session.get(url_search) as resp:
            result = await resp.json()
        try:
            isrc = result["tracks"][0]["external"]["isrc"]
            spotify_id = result["tracks"][0]["external"]["spotify_id"]
        except KeyError as e:
            raise LyricsNotFound from e

        url_lyrics = f"https://api.flowery.pw/v1/lyrics?isrc={isrc}&spotify_id={spotify_id}&query={q}"

        async with inter.client.session.get(url_lyrics) as res:
            lyrics = await res.json()

        try:
            lyrics_text = lyrics["lyrics"]["text"]
            title = lyrics["track"]["title"]
            artist = lyrics["track"]["artist"]
            thumbnail = lyrics["track"]["media"]["artwork"]
        except KeyError as e:
            raise LyricsNotFound from e

        lyrics_text = truncate(lyrics_text, length=4096)

        embed = Embed(title=title, description=lyrics_text, timestamp=utcnow())
        embed.set_author(name=artist)
        embed.set_thumbnail(url=thumbnail)
        await inter.send(embed=embed, ephemeral=True)
