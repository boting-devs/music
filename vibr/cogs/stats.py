from __future__ import annotations

from asyncio import sleep
from statistics import mean
from typing import TYPE_CHECKING

from nextcord.ext.commands import Cog
from nextcord.ext.tasks import loop
from nextcord.utils import utcnow
from pomice import NoNodesAvailable

if TYPE_CHECKING:
    from vibr.__main__ import Vibr


class Stats(Cog):
    def __init__(self, bot: Vibr) -> None:
        self.bot = bot

        self.active_player_count: list[int] = []
        self.total_player_count: list[int] = []
        self.lavalink_load: list[int] = []
        self.system_load: list[int] = []
        self.memory_used: list[int] = []
        self.memory_allocated: list[int] = []
        self.memory_percentage: list[int] = []

        self.hourly_stats.start()
        self.minute_stats.start()

    def cog_unload(self) -> None:
        self.hourly_stats.stop()
        self.minute_stats.stop()

    @loop(hours=1)
    async def hourly_stats(self):
        if not len(self.active_player_count):
            # There are no data points, return because this is probably too early.
            return

        guilds = len(self.bot.guilds)

        active_players = mean(self.active_player_count)
        total_players = mean(self.total_player_count)
        lavalink_load = mean(self.lavalink_load)
        system_load = mean(self.system_load)
        memory_used = mean(self.memory_used)
        memory_allocated = mean(self.memory_allocated)
        memory_percentage = mean(self.memory_percentage)

        now = utcnow()

        hour = now.hour + 1
        if hour == 24:
            hour = 0

        time = now.replace(second=0, microsecond=0, minute=0, hour=hour)

        await self.bot.db.execute(
            """INSERT INTO hourly_stats
                (time,
                 guilds,
                 active_players,
                 total_players,
                 lavalink_load,
                 system_load,
                 memory_used,
                 memory_allocated,
                 memory_percentage,
                 commands)

            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9,
                (SELECT SUM(amount) FROM commands)
            )
            """,
            time,
            guilds,
            active_players,
            total_players,
            lavalink_load,
            system_load,
            memory_used,
            memory_allocated,
            memory_percentage,
        )
        self.active_player_count.clear()
        self.total_player_count.clear()
        self.lavalink_load.clear()
        self.system_load.clear()
        self.memory_used.clear()
        self.memory_allocated.clear()
        self.memory_percentage.clear()

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

    @loop(minutes=1)
    async def minute_stats(self):
        # Set default to None so IDEs are happy it isn't undefined.
        stats = None

        # Try getting stats 5 times, if it fails we always have the next loop anyway.
        for tries in range(5):
            try:
                node = self.bot.pool.get_node()
            except NoNodesAvailable:
                await sleep(2.5 * tries)
            else:
                stats = node.stats

        # IDEs should be happy now.
        assert stats is not None

        self.active_player_count.append(stats.players_active or 0)
        self.total_player_count.append(stats.players_total or 0)
        self.lavalink_load.append(stats.cpu_process_load or 0)
        self.system_load.append(stats.cpu_system_load or 0)
        # Lavalink uses bytes, this is MiB
        self.memory_used.append((stats.used or 0) // (1024**2))
        self.memory_allocated.append((stats.allocated or 0) // (1024**2))
        self.memory_percentage.append(
            int((stats.used or 0) / (stats.reservable or 0) * 100)
        )

    @minute_stats.before_loop
    async def wait_until_next_minute(self):
        await self.bot.wait_until_ready()
        now = utcnow()
        # Round up to the next minute from now, then wait for that many seconds.
        minute = now.minute + 1

        # Loop back if :60, as min 60 does not exist.
        if minute == 60:
            minute = 0

        time = now.replace(second=0, microsecond=0, minute=minute, hour=now.hour)

        wait_time = time - now
        await sleep(wait_time.total_seconds())


def setup(bot: Vibr):
    bot.add_cog(Stats(bot))
