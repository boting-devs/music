from __future__ import annotations

from asyncio import sleep
from statistics import mean

from botbase import CogBase, CommandLog
from nextcord.ext.tasks import loop
from nextcord.utils import utcnow

from vibr.bot import Vibr
from vibr.db import HourlyStats, NodeStats


class StatsCollection(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)

        # node: set[average stats]
        self.active_player_count: dict[str, set[int]] = {}
        self.total_player_count: dict[str, set[int]] = {}
        self.lavalink_load: dict[str, set[int]] = {}
        self.system_load: dict[str, set[int]] = {}
        self.memory_used: dict[str, set[int]] = {}
        self.memory_allocated: dict[str, set[int]] = {}
        self.memory_percentage: dict[str, set[int]] = {}
        self.listeners: set[int] = set()

        self.minute_stats.start()
        self.hourly_stats.start()

    @loop(minutes=1)
    async def minute_stats(self):
        for node in self.bot.pool.nodes:
            stats = node.stats

            if stats is None:
                continue

            active_player_count = self.active_player_count.get(node.label, set())
            total_player_count = self.total_player_count.get(node.label, set())
            lavalink_load = self.lavalink_load.get(node.label, set())
            system_load = self.system_load.get(node.label, set())
            memory_used = self.memory_used.get(node.label, set())
            memory_allocated = self.memory_allocated.get(node.label, set())
            memory_percentage = self.memory_percentage.get(node.label, set())

            active_player_count.add(stats.playing_player_count)
            total_player_count.add(stats.player_count)
            lavalink_load.add(stats.cpu.lavalink_load)
            system_load.add(stats.cpu.system_load)
            memory_used.add(stats.memory.used)
            memory_allocated.add(stats.memory.allocated)
            memory_percentage.add(stats.memory.reservable)

            self.active_player_count[node.label] = active_player_count
            self.total_player_count[node.label] = total_player_count
            self.lavalink_load[node.label] = lavalink_load
            self.system_load[node.label] = system_load
            self.memory_used[node.label] = memory_used
            self.memory_allocated[node.label] = memory_allocated
            self.memory_percentage[node.label] = memory_percentage

        # TODO: count listeners
        self.listeners.add(69)

    @loop(hours=1)
    async def hourly_stats(self):
        if not self.active_player_count:
            return

        time = utcnow()

        await HourlyStats.objects.create(
            time=time,
            guilds=len(self.bot.guilds),
            commands=await CommandLog.objects.count(),
            # total_songs=await Song.objects.count(),
            # TODO: add song count
            total_songs=69,
            listeners=len(self.listeners),
        )

        for node in self.bot.pool.nodes:
            stats = node.stats

            if stats is None:
                continue

            try:
                active_player_count = mean(self.active_player_count[node.label])
                total_player_count = mean(self.total_player_count[node.label])
                lavalink_load = mean(self.lavalink_load[node.label])
                system_load = mean(self.system_load[node.label])
                memory_used = mean(self.memory_used[node.label])
                memory_allocated = mean(self.memory_allocated[node.label])
                memory_percentage = mean(self.memory_percentage[node.label])
            except KeyError:
                continue

            await NodeStats.objects.create(
                time=time,
                node=node.label,
                active_players=active_player_count,
                total_players=total_player_count,
                lavalink_load=lavalink_load,
                system_load=system_load,
                memory_used=memory_used,
                memory_allocated=memory_allocated,
                memory_percentage=memory_percentage,
            )

    @hourly_stats.before_loop
    async def wait_until_next_hour(self):
        await self.bot.wait_until_ready()
        now = utcnow()
        # Round up to the next hour from now, then wait for that many seconds.

        hour = now.hour + 1
        if hour == 24:
            hour = 0

        time = now.replace(second=0, microsecond=0, minute=0, hour=hour)

        wait_time = time - now
        await sleep(wait_time.total_seconds())


def setup(bot: Vibr) -> None:
    bot.add_cog(StatsCollection(bot))
