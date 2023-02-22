from __future__ import annotations

from nextcord import PartialInteractionMessage
from nextcord.ui import Button, Select, View


class TimeoutView(View):
    message: PartialInteractionMessage | None = None

    async def on_timeout(self):
        self.stop()

        for child in self.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)
