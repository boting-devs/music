from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ui import Button, Select, View

if TYPE_CHECKING:
    from nextcord import PartialInteractionMessage


class TimeoutView(View):
    message: PartialInteractionMessage | None = None

    async def on_timeout(self) -> None:
        self.stop()

        for child in self.children:
            if isinstance(child, Button | Select):
                child.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)
