from __future__ import annotations

from botbase import CogBase, CommandLog
from nextcord import Embed, slash_command

from vibr.bot import Vibr
from vibr.inter import Inter

MAIN_STATS = """
Guilds: `{guilds:,}`
Commands Used `{commands:,}`
Songs Played: `{songs:,}`
Active Players: `{active_players:,}`
Total Players: `{total_players:,}`
Users Listening: `{listeners:,}`
""".strip()


class PublicStats(CogBase[Vibr]):
    @slash_command(name="bot-stats", dm_permission=False)
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
    bot.add_cog(PublicStats(bot))
