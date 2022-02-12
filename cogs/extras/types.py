from __future__ import annotations

import botbase
import pomice
import nextcord


class Player(pomice.Player):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.queue: list[pomice.Track] = []


class MyContext(botbase.MyContext):
    voice_client: Player


class FakeGuild(nextcord.Guild):
    voice_client: Player


class MyInter(botbase.MyInter):
    guild: FakeGuild | None
