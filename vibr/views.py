from __future__ import annotations

from time import gmtime, strftime
from typing import TYPE_CHECKING

from nextcord import SelectOption
from nextcord.ui import Button, Select, View

from vibr.embed import Embed
from vibr.inter import Inter
from vibr.utils import truncate

if TYPE_CHECKING:
    from mafic import Track
    from nextcord import PartialInteractionMessage


class TimeoutView(View):
    message: PartialInteractionMessage | Inter | None = None

    async def on_timeout(self) -> None:
        self.stop()

        for child in self.children:
            if isinstance(child, Button | Select):
                child.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)


class SearchSelect(Select["SearchView"]):
    def __init__(self, tracks: list[Track]) -> None:
        super().__init__(
            placeholder="Select a track.",
            options=[
                SelectOption(
                    label=truncate(
                        f"{i+1}. {track.title} - {track.author}",
                        length=100,
                    ),
                    value=str(i),
                )
                for i, track in enumerate(tracks)
            ],
        )

        self.inter: Inter | None = None

    async def callback(self, _: Inter) -> None:
        assert self.view is not None
        self.view.selected_track = int(self.values[0])
        self.view.stop()


class SearchView(TimeoutView):
    def __init__(self, tracks: list[Track]) -> None:
        super().__init__(timeout=60)

        self.selected_track: int | None = None
        self.add_item(SearchSelect(tracks))

    @staticmethod
    def create_search_embed(*, tracks: list[Track]) -> Embed:
        return Embed(
            title="Search Results",
            description="\n".join(
                f"**{i+1}.** [**{t.title}**]({t.uri}) by "
                f"**{t.author}** "
                f"[{strftime('%H:%M:%S', gmtime((t.length or 0) / 1000))}]"
                for i, t in enumerate(tracks)
            ),
        )
