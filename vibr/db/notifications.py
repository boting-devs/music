from __future__ import annotations

from piccolo.columns import Serial, Text, Timestamptz
from piccolo.table import Table


class Notification(Table):
    id = Serial(primary_key=True)
    title = Text()
    description = Text()
    posted = Timestamptz()
    expires = Timestamptz()
