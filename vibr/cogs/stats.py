from __future__ import annotations

from asyncio import sleep
from contextlib import suppress
from statistics import mean
from typing import TYPE_CHECKING, cast

from asyncpg import UniqueViolationError
from botbase import MyContext
from nextcord import Embed
from nextcord.channel import VocalGuildChannel
from nextcord.ext.commands import Cog, command, is_owner
from nextcord.ext.tasks import loop
from nextcord.utils import utcnow
from pomice import NoNodesAvailable

from .extras.views import StatsView

if TYPE_CHECKING:
    from vibr.__main__ import Vibr


STATS: str = """
Guilds: `{guilds:,}`
Commands Used: `{commands:,}`
Songs Played: `{songs:,}`
Active Players: `{active_players:,}`
Total Players: `{total_players:,}`
Users Listening: `{listeners:,}`
Lavalink Load: `{process_load:.3f}`
System Load: `{system_load:.3f}`
Memory Used: `{memory_used:,}MiB`
Memory Allocated: `{memory_allocated:,}MiB`
Memory %: `{memory_percentage:.0f}%`
""".strip()


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
        self.listeners: list[int] = []

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
        listeners = mean(self.listeners)

        now = utcnow()

        hour = now.hour + 1
        if hour == 24:
            hour = 0

        time = now.replace(second=0, microsecond=0, minute=0, hour=hour)

        with suppress(UniqueViolationError):
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
                    listeners,
                    commands,
                    total_songs)

                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    (SELECT SUM(amount) FROM commands), (SELECT SUM(amount) FROM songs)
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
                listeners,
            )
            self.active_player_count.clear()
            self.total_player_count.clear()
            self.lavalink_load.clear()
            self.system_load.clear()
            self.memory_used.clear()
            self.memory_allocated.clear()
            self.memory_percentage.clear()
            self.listeners.clear()

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

        [v.channel.id for v in self.bot.voice_clients]  # type: ignore
        self.listeners.append(
            sum(
                len(cast(VocalGuildChannel, player.channel).voice_states)
                for player in self.bot.voice_clients
            )
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

    @command()
    @is_owner()
    async def stats(self, ctx: MyContext):
        view = StatsView(ctx)
        m = await ctx.send(view=view)
        view.message = m
        await view.update()

    @command(name="cstats")
    @is_owner()
    async def current_stats(self, ctx: MyContext):
        # FIXME: remove duplication of similar code
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

        guilds = len(self.bot.guilds)
        commands = await self.bot.db.fetchval("SELECT SUM(amount) FROM commands")
        songs = await self.bot.db.fetchval("SELECT SUM(amount) FROM songs")

        [v.channel.id for v in self.bot.voice_clients]  # type: ignore

        embed = Embed(
            title="Current Stats",
            description=STATS.format(
                guilds=guilds,
                commands=commands,
                songs=songs,
                active_players=stats.players_active or 0,
                total_players=stats.players_total or 0,
                process_load=stats.cpu_process_load or 0,
                system_load=stats.cpu_system_load or 0,
                memory_used=(stats.used or 0) // (1024**2),
                memory_allocated=(stats.allocated or 0) // (1024**2),
                memory_percentage=int(
                    (stats.used or 0) / (stats.reservable or 0) * 100
                ),
                listeners=sum(
                    len(cast(VocalGuildChannel, player.channel).voice_states)
                    for player in self.bot.voice_clients
                ),
            ),
            color=self.bot.color,
        )

        await ctx.send(embed=embed)


def setup(bot: Vibr):
    bot.add_cog(Stats(bot))
