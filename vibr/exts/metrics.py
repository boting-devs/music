from __future__ import annotations

from asyncio import sleep

from botbase import CogBase
from botbase.db import CommandLog
from nextcord.ext.tasks import loop
from prometheus_async.aio.web import MetricsHTTPServer, start_http_server
from prometheus_client import Gauge, Info

from vibr.bot import Vibr
from vibr.db import SongLog
from vibr.sharding import CURRENT_CLUSTER


class Prometheus(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)
        self.metrics: MetricsHTTPServer | None = None

        if CURRENT_CLUSTER == 0:
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

            if CURRENT_CLUSTER != 0:
                return

            self.metric_collection.start()
            await self.bot.nodes_connected.wait()

            info = Info("node", "Info about a node", labelnames=["node"])
            playing_player_count = Gauge(
                "node_playing_player_count", "Total active players", labelnames=["node"]
            )
            player_count = Gauge(
                "node_total_player_count",
                "Total connected players",
                labelnames=["node"],
            )
            cpu_system_load = Gauge(
                "node_cpu_system_load",
                "CPU Load of the system the node is on",
                labelnames=["node"],
            )
            cpu_lavalink_load = Gauge(
                "node_cpu_load", "CPU Load of the Lavalink process", labelnames=["node"]
            )
            memory_free = Gauge(
                "node_memory_free_bytes", "Total free node memory", labelnames=["node"]
            )
            memory_used = Gauge(
                "node_memory_used_bytes", "Total used node memory", labelnames=["node"]
            )
            memory_allocated = Gauge(
                "node_memory_allocated_bytes",
                "Total allocated node memory",
                labelnames=["node"],
            )
            frame_stats_send = Gauge(
                "node_frames_sent", "Total UDP frames sent", labelnames=["node"]
            )
            frame_stats_nulled = Gauge(
                "node_frames_nulled", "Total UDP frames nulled", labelnames=["node"]
            )
            frame_stats_deficit = Gauge(
                "node_frames_deficit", "Total UDP frames deficit", labelnames=["node"]
            )

            for node in self.bot.pool.nodes:
                while not node.stats:
                    await sleep(0.1)
                info.labels(node=node.label).info(
                    {
                        "node_cpu_cores": str(node.stats.cpu.cores),
                        "node_memory_reservable": str(node.stats.memory.reservable),
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
                frame_stats_send.labels(node=node.label).set_function(
                    lambda node=node: node.stats.frame_stats.sent if node.stats else 0
                )
                frame_stats_nulled.labels(node=node.label).set_function(
                    lambda node=node: node.stats.frame_stats.nulled if node.stats else 0
                )
                frame_stats_deficit.labels(node=node.label).set_function(
                    lambda node=node: (
                        node.stats.frame_stats.deficit if node.stats else 0
                    )
                )

    async def cog_unload(self) -> None:
        if self.metrics:
            await self.metrics.close()

        self.metric_collection.stop()


def setup(bot: Vibr) -> None:
    bot.add_cog(Prometheus(bot))