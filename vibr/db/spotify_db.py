# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import BaseMeta
from ormar import DateTime, ForeignKey, Integer, Model, SmallInteger, String , Boolean

if TYPE_CHECKING:
    from datetime import datetime

class Spotifydb(Model):
    class Meta(BaseMeta):
        tablename = "users"

    id:int = Integer(primary_key = True)
    spotify:str = String()
    