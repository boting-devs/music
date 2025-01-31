# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

from piccolo.columns import BigInt, Boolean, Text, Timestamptz
from piccolo.table import Table


# "user" is reserved and special
class User(Table, tablename="users"):
    id = BigInt(primary_key=True)
    spotify_id = Text(null=True, default=None)
    notified = Boolean()
    notifications = Boolean(default=True)
    topgg_voted = Timestamptz(null=True, default=None)
