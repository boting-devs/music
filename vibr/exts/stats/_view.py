from __future__ import annotations

from datetime import timedelta
from enum import Enum
from io import BytesIO
from random import sample
from typing import TYPE_CHECKING

from cycler import cycler
from matplotlib import rc_context
from matplotlib.dates import DateFormatter
from matplotlib.pyplot import close, savefig, subplots
from nextcord import Embed, File, Interaction, SelectOption
from nextcord.ui import StringSelect, string_select
from nextcord.utils import utcnow

from vibr.db import HourlyStats, NodeStats
from vibr.views import TimeoutView

if TYPE_CHECKING:
    from vibr.bot import Vibr


class StatsTime(Enum):
    """The time of stats to show."""

    ALL = str(timedelta(days=10**4).total_seconds())
    DAY = str(timedelta(days=1).total_seconds())
    WEEK = str(timedelta(days=7).total_seconds())
    MONTH = str(timedelta(days=30).total_seconds())


class StatsType(Enum):
    """The type of stats to show."""

    GUILDS = "guilds"
    COMMANDS = "commands"
    SONGS = "total_songs"


class NodeStatsType(Enum):
    """Node-scoped stats."""

    PLAYERS = "active_players, total_players, listeners"
    LOAD = "lavalink_load, system_load"
    MEMORY = "memory_used, memory_allocated, memory_percentage"


TYPE_TO_TITLE: dict[StatsType | NodeStatsType, str] = {
    StatsType.GUILDS: "Guild Count",
    StatsType.COMMANDS: "Commands Used",
    StatsType.SONGS: "Songs Played",
    NodeStatsType.PLAYERS: "Players/Listeners",
    NodeStatsType.LOAD: "CPU Load",
    NodeStatsType.MEMORY: "Memory Usage (MiB/%)",
}


class NodeSelection(StringSelect["StatsView"]):
    def __init__(self, bot: Vibr) -> None:
        super().__init__(
            options=[SelectOption(label=node.label) for node in bot.pool.nodes],
            placeholder="Select a node.",
        )

    async def callback(self, _: Interaction) -> None:
        assert self.view is not None

        await self.view.update_node(self.values[0])


class StatsView(TimeoutView):
    def __init__(self, bot: Vibr) -> None:
        super().__init__()
        self.bot = bot

        self.timeframe = StatsTime.ALL
        self.type = StatsType.GUILDS
        self.node = "LOCAL"

        self.add_item(NodeSelection(bot))

    @string_select(
        placeholder="Select a timeframe.",
        options=[
            SelectOption(label=name.title(), value=enum.value)
            for name, enum in StatsTime.__members__.items()
        ],
        min_values=1,
        max_values=1,
    )
    async def timeframe_select(self, select: StringSelect, inter: Interaction) -> None:
        await inter.response.defer()
        await self.update_stats_time(select.values[0])

    @string_select(
        placeholder="Select a type.",
        options=[
            SelectOption(label=name.title(), value=enum.value)
            for name, enum in StatsType.__members__.items()
        ],
        min_values=1,
        max_values=1,
    )
    async def type_select(self, select: StringSelect, inter: Interaction) -> None:
        await inter.response.defer()
        await self.update_stats_type(select.values[0])

    async def update_stats_type(self, value: str) -> None:
        self.type = StatsType(value)
        await self.update()

    async def update_stats_time(self, value: str) -> None:
        self.timeframe = StatsTime(value)
        await self.update()

    async def update_node(self, value: str) -> None:
        self.node = value
        await self.update()

    async def update(self) -> None:
        embed, file = await self.get_graph()
        assert self.message is not None
        await self.message.edit(embed=embed, file=file)

    async def get_graph(self) -> tuple[Embed, File]:
        if self.type in NodeStatsType:
            data = await NodeStats.objects.all(
                time__gt=utcnow() - timedelta(seconds=float(self.timeframe.value))
            )
        else:
            data = await HourlyStats.objects.all(
                time__gt=utcnow() - timedelta(seconds=float(self.timeframe.value))
            )

        # should be list[NodeStats] | list[HourlyStats]
        # https://github.com/microsoft/pyright/issues/4660#issuecomment-1435733099
        new_data: list[NodeStats | HourlyStats] = []
        collected: HourlyStats | NodeStats | None = None
        for row in data:
            time = row.time

            if time.hour == 0:
                if collected:
                    new_data.append(collected)

                row.time = time + timedelta(days=1)
                collected = row
            else:
                new_data.append(row)

        embed = Embed(title="Stats", color=self.bot.colour)

        colours = [f"#{hex(c)[2:]}" for c in self.bot.colours]
        with rc_context(
            {
                "axes.prop_cycle": cycler(color=sample(colours, len(colours))),
                "figure.constrained_layout.use": True,
                "axes.facecolor": "#272934",
                "axes.edgecolor": "white",
                "figure.facecolor": "black",
                "axes.labelcolor": "white",
                "xtick.color": "white",
                "ytick.color": "white",
                "text.color": "white",
                "legend.framealpha": 1,
            }
        ):
            figure, axes = subplots()
            axes.set_title(
                f"{TYPE_TO_TITLE[self.type]} ({self.timeframe.name.title()})"
            )

            times = [row.time for row in data]

            if self.timeframe is StatsTime.WEEK:
                # Wed 13
                date_form = DateFormatter("%a %d")
            elif self.timeframe is StatsTime.DAY:
                # 23:
                date_form = DateFormatter("%H:")
            else:
                # 13-11
                date_form = DateFormatter("%d-%m")

            axes.xaxis.set_major_formatter(date_form)

            handles = [
                axes.plot(
                    times,
                    [getattr(row, t) for row in data],
                    label=t.replace("_", " ").title(),
                )[0]
                for t in self.type.value.split(", ")
            ]
            axes.legend(handles=handles)

            b = BytesIO()

            try:
                savefig(b, format="png", bbox_inches="tight")
            finally:
                close()

        b.seek(0)
        file = File(
            b,
            filename="stats.png",
            description=(
                f"Stats for {self.type.value} "
                f"over the last {self.timeframe.name.lower()}."
            ),
        )
        embed.set_image("attachment://stats.png")

        return embed, file
