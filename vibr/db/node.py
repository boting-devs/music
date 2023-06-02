from __future__ import annotations

from piccolo.columns import Text, Varchar
from piccolo.table import Table


class Node(Table):
    label = Text(primary_key=True)
    session_id = Varchar(16)
