from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ui import Button, View, Select
from nextcord import SelectOption, Interaction

if TYPE_CHECKING:
    from nextcord import Emoji, PartialEmoji, Message

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
    message: Message
    uri: str | None

    def __init__(self, playlists: SpotifyPlaylists) -> None:
        items = playlists["items"]
        chunks = [items[i : i + 10] for i in range(0, len(items), 25)]

        for chunk in chunks:
            self.add_item(PlaylistSelect(chunk))

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        await self.message.edit(view=self)


class PlaylistSelect(Select):
    def __init__(self, chunk: list[Playlist]) -> None:
        super().__init__(
            placeholder="Select a playlist",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(
                    label=p["name"], description=p["description"], value=p["url"]
                )
                for p in chunk
            ],
        )
        self.view.uri = None

    async def callback(self, interaction: Interaction) -> None:
        self.view.url = self.values[0]
        assert self.view is not None

        for child in self.view.children:
            child.disabled = True

        await interaction.response.edit_message(view=self.view)

        self.view.stop()
