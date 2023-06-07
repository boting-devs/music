from __future__ import annotations

from piccolo.columns import Serial, SmallInt, Text, Varchar
from piccolo.table import Table


class Node(Table):
    id = Serial(primary_key=True)
    label = Text()
    session_id = Varchar(16)
    cluster = SmallInt()
