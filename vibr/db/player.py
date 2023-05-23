from __future__ import annotations

from piccolo.columns import BigInt, SmallInt
from piccolo.table import Table


class PlayerConfig(Table):
    channel_id = BigInt(primary_key=True)
    volume = SmallInt()
