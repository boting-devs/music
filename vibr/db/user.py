# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

from botbase import BaseMeta
from ormar import BigInteger, Model, Text


class User(Model):
    class Meta(BaseMeta):
        tablename = "users"

    id: int = BigInteger(primary_key=True, autoincrement=False)
    spotify_id: str | None = Text(nullable=True)
