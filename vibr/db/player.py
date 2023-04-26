# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

from botbase import BaseMeta
from ormar import BigInteger, Model, SmallInteger


class PlayerConfig(Model):
    class Meta(BaseMeta):
        tablename = "players"

    channel_id: int = BigInteger(primary_key=True, autoincrement=False)
    volume: int = SmallInteger(minimum=0, maximum=500)
