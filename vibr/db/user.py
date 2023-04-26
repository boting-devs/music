# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

from botbase import BaseMeta
from ormar import BigInteger, Model, String


class User(Model):
    class Meta(BaseMeta):
        tablename = "users"

    id: int = BigInteger(primary_key=True, autoincrement=False)
    spotify: str = String(max_length=50)
