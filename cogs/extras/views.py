from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ui import Button, View, Select
from nextcord import SelectOption, Interaction

if TYPE_CHECKING:
    from nextcord import Emoji, PartialEmoji, Message

    from .types import Playlist


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

    def __init__(self, playlists: list[Playlist]) -> None:
        super().__init__()
        chunks = [playlists[i : i + 10] for i in range(0, len(playlists), 25)]

        for chunk in chunks:
            self.add_item(PlaylistSelect(chunk))

        self.uri = None

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        await self.message.edit(view=self)


class PlaylistSelect(Select[PlaylistView]):
    def __init__(self, chunk: list[Playlist]) -> None:
        super().__init__(
            placeholder="Select a playlist",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(
                    label=(p["name"] or "No name defined?"),
                    description=(
                        (
                            p["description"]
                            if len(p["description"]) < 100
                            else p["description"][:97] + "..."
                        )
                        if p["description"]
                        else None
                    ),
                    value=p["external_urls"]["spotify"] or p["url"],
                )
                for p in chunk
            ],
        )

    async def callback(self, interaction: Interaction) -> None:
        assert self.view is not None
        self.view.uri = self.values[0]

        print(f"values: {self.values}")

        for child in self.view.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        await interaction.response.edit_message(view=self.view)

        self.view.stop()
