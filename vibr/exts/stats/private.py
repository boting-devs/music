from __future__ import annotations

from botbase import CogBase, CommandLog
from nextcord import Embed, slash_command
from nextcord.ext.application_checks import is_owner

from vibr.bot import GUILD_IDS, Vibr
from vibr.inter import Inter

MAIN_STATS = """
Guilds: `{guilds:,}`
Commands Used `{commands:,}`
Songs Played: `{songs:,}`
Active Players: `{active_players:,}`
Total Players: `{total_players:,}`
Users Listening: `{listeners:,}`
""".strip()


NODE_STATS = """
Active Players: `{active_players:,}`
Total Players: `{total_players:,}`
Lavalink Load: `{process_load:.1f}%`
System Load: `{system_load:.1f}%`
Memory Used: `{memory_used:,}MiB`
Memory Allocated: `{memory_allocated:,}MiB`
Memory %: `{memory_percentage:.0f}%`
""".strip()


class PrivateStats(CogBase[Vibr]):
    @slash_command(name="node-stats", default_member_permissions=8, guild_ids=GUILD_IDS)
    @is_owner()
    async def node_stats(self, inter: Inter) -> None:
        """Get stats about all nodes."""

        embed = Embed(colour=self.bot.colour)
        guilds = len(self.bot.guilds)
        commands = await CommandLog.count()
        # TODO: songs
        songs = 69

        # TODO: listeners
        listeners = 69

        active_players = 0
        total_players = 0

        for node in self.bot.pool.nodes:
            stats = node.stats
            if not stats:
                continue

            active_players += stats.playing_player_count
            total_players += stats.player_count

            embed.add_field(
                name=node.label,
                value=NODE_STATS.format(
                    active_players=stats.playing_player_count,
                    total_players=stats.player_count,
                    process_load=stats.cpu.lavalink_load * 100,
                    system_load=stats.cpu.system_load * 100,
                    memory_used=stats.memory.used // (1024**2),
                    memory_allocated=stats.memory.allocated // (1024**2),
                    memory_percentage=(stats.memory.used / stats.memory.reservable)
                    * 100,
                ),
            )

        embed.description = MAIN_STATS.format(
            guilds=guilds,
            commands=commands,
            songs=songs,
            active_players=active_players,
            total_players=total_players,
            listeners=listeners,
        )

        await inter.response.send_message(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(PrivateStats(bot))
