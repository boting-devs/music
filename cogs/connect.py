from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ext.commands import Cog

if TYPE_CHECKING:
    from ..mmain import MyBot


class Music(Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot


def setup(bot: MyBot):
    bot.add_cog(Music(bot))
