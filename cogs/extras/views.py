from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ui import Button, View, Select
from nextcord import SelectOption

if TYPE_CHECKING:
    from nextcord import Emoji, PartialEmoji

    from .types import SpotifyPlaylists, Playlist


class LinkButtonView(View):
    def __init__(
        self, name: str, url: str, emoji: str | PartialEmoji | Emoji | None = None
    ):
        super().__init__()
        if emoji is not None:
            self.add_item(Button(label=name, url=url, emoji=emoji))
        else:
            self.add_item(Button(label=name, url=url))


class PlaylistView(View):
    def __init__(self, playlists: SpotifyPlaylists) -> None:
        items = playlists["items"]
        chunks = [items[i : i + 10] for i in range(0, len(items), 25)]

        for chunk in chunks:
            self.add_item(PlaylistSelect(chunk))


class PlaylistSelect(Select):
    def __init__(self, chunk: list[Playlist]) -> None:
        super().__init__(
            placeholder="Select a playlist",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(label=p["name"], description=p["description"])
                for p in chunk
            ]
        )
