from __future__ import annotations

from asyncio import sleep
from typing import cast

from botbase import CogBase
from botbase.db import CommandLog
from nextcord.channel import VocalGuildChannel
from nextcord.ext.tasks import loop
from prometheus_async.aio.web import MetricsHTTPServer, start_http_server
from prometheus_client import Gauge, Info

from vibr.bot import Vibr
from vibr.db import SongLog
from vibr.sharding import CURRENT_CLUSTER

CURRENT_CLUSTER = int(CURRENT_CLUSTER)


class Prometheus(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)
        self.metrics: MetricsHTTPServer | None = None

        if CURRENT_CLUSTER == 1:
            self.commands = Gauge("vibr_commands_used", "Total command invokations")
            self.songs = Gauge("vibr_songs_played", "Total songs played")

    @loop(seconds=30)
    async def metric_collection(self) -> None:
        self.commands.set(await CommandLog.count())
        self.songs.set(await SongLog.count())

    @CogBase.listener()
    async def on_ready(self) -> None:
        if not self.metrics:
            self.metrics = await start_http_server(port=9000)

            guilds = Gauge(
                "vibr_guilds",
                "Total guild count in this cluster",
                labelnames=["cluster"],
            )
            listeners = Gauge(
                "vibr_listeners",
                "Total listeners from all players in this cluster",
                labelnames=["cluster"],
            )

            guilds.labels(cluster=CURRENT_CLUSTER).set_function(
                lambda: len(self.bot.guilds)
            )
            listeners.labels(cluster=CURRENT_CLUSTER).set_function(
                lambda: (
                    sum(
                        max(
                            # Take off vibr, or if somehow its 0, keep it at 0.
                            len(cast(VocalGuildChannel, player.channel).voice_states)
                            - 1,
                            0,
                        )
                        for player in self.bot.voice_clients
                    )
                )
            )

            if CURRENT_CLUSTER != 1:
                return

            self.metric_collection.start()
            await self.bot.nodes_connected.wait()

            info = Info("lavalink", "Info about a node", labelnames=["node"])
            playing_player_count = Gauge(
                "lavalink_playing_player_count",
                "Total active players",
                labelnames=["node"],
            )
            player_count = Gauge(
                "lavalink_total_player_count",
                "Total connected players",
                labelnames=["node"],
            )
            cpu_system_load = Gauge(
                "lavalink_cpu_system_load",
                "CPU Load of the system the node is on",
                labelnames=["node"],
            )
            cpu_lavalink_load = Gauge(
                "lavalink_cpu_load",
                "CPU Load of the Lavalink process",
                labelnames=["node"],
            )
            memory_free = Gauge(
                "lavalink_memory_free_bytes",
                "Total free node memory",
                labelnames=["node"],
            )
            memory_used = Gauge(
                "lavalink_memory_used_bytes",
                "Total used node memory",
                labelnames=["node"],
            )
            memory_allocated = Gauge(
                "lavalink_memory_allocated_bytes",
                "Total allocated node memory",
                labelnames=["node"],
            )
            memory_reservable = Gauge(
                "lavalink_memory_reservable_bytes",
                "Total reservable node memory",
                labelnames=["node"],
            )
            frame_stats_send = Gauge(
                "lavalink_frames_sent", "Total UDP frames sent", labelnames=["node"]
            )
            frame_stats_nulled = Gauge(
                "lavalink_frames_nulled", "Total UDP frames nulled", labelnames=["node"]
            )
            frame_stats_deficit = Gauge(
                "lavalink_frames_deficit",
                "Total UDP frames deficit",
                labelnames=["node"],
            )

            for node in self.bot.pool.nodes:
                while not node.stats:
                    await sleep(0.1)
                info.labels(node=node.label).info(
                    {
                        "lavalink_cpu_cores": str(node.stats.cpu.cores),
                        "lavalink_memory_reservable": str(node.stats.memory.reservable),
                    }
                )
                # Funny syntax innit?
                # https://docs.python-guide.org/writing/gotchas/#late-binding-closures
                playing_player_count.labels(node=node.label).set_function(
                    lambda node=node: (
                        node.stats.playing_player_count if node.stats else 0
                    )
                )
                player_count.labels(node=node.label).set_function(
                    lambda node=node: node.stats.player_count if node.stats else 0
                )
                cpu_system_load.labels(node=node.label).set_function(
                    lambda node=node: node.stats.cpu.system_load if node.stats else 0
                )
                cpu_lavalink_load.labels(node=node.label).set_function(
                    lambda node=node: node.stats.cpu.lavalink_load if node.stats else 0
                )
                memory_free.labels(node=node.label).set_function(
                    lambda node=node: node.stats.memory.free if node.stats else 0
                )
                memory_used.labels(node=node.label).set_function(
                    lambda node=node: node.stats.memory.used if node.stats else 0
                )
                memory_allocated.labels(node=node.label).set_function(
                    lambda node=node: node.stats.memory.allocated if node.stats else 0
                )
                memory_reservable.labels(node=node.label).set_function(
                    lambda node=node: node.stats.memory.reservable if node.stats else 0
                )
                frame_stats_send.labels(node=node.label).set_function(
                    lambda node=node: node.stats.frame_stats.sent
                    if node.stats and node.stats.frame_stats
                    else 0
                )
                frame_stats_nulled.labels(node=node.label).set_function(
                    lambda node=node: node.stats.frame_stats.nulled
                    if node.stats and node.stats.frame_stats
                    else 0
                )
                frame_stats_deficit.labels(node=node.label).set_function(
                    lambda node=node: (
                        node.stats.frame_stats.deficit
                        if node.stats and node.stats.frame_stats
                        else 0
                    )
                )

    def cog_unload(self) -> None:
        if self.metrics:
            self.bot.loop.create_task(self.metrics.close())

        self.metric_collection.stop()


def setup(bot: Vibr) -> None:
    bot.add_cog(Prometheus(bot))
