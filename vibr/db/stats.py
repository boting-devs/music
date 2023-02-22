# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

from datetime import datetime

from botbase import BaseMeta
from ormar import DateTime, ForeignKey, Integer, Model, SmallInteger, String


class HourlyStats(Model):
    class Meta(BaseMeta):
        tablename = "hourly_stats"

    time: datetime = DateTime(primary_key=True, timezone=True)
    guilds: int = Integer()
    commands: int = Integer()
    total_songs: int = Integer()
    listeners: int = Integer()
    nodes: list[NodeStats]


class NodeStats(Model):
    class Meta(BaseMeta):
        tablename = "node_stats"

    time: datetime = ForeignKey(
        HourlyStats, primary_key=True, related_name="nodes", ondelete="CASCADE"
    )
    node: str = String(max_length=25, primary_key=True)
    active_players: int = Integer()
    total_players: int = Integer()
    lavalink_load: int = SmallInteger()
    system_load: int = SmallInteger()
    memory_used: int = SmallInteger()
    memory_allocated: int = SmallInteger()
    memory_percentage: int = SmallInteger()
