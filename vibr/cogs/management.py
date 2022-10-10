from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import MyInter
from nextcord import Colour, Embed
from nextcord.ext.commands import Cog, command, is_owner

from .extras.types import MyContext, Player

if TYPE_CHECKING:
    from ..__main__ import Vibr


class Management(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot

    @command()
    @is_owner()
    async def shutdown(self, ctx: MyContext, eta: str, *, reason: str):
        for voice_client in self.bot.voice_clients:
            assert isinstance(voice_client, Player)

            if voice_client.current is not None:
                inter = voice_client.current.ctx
                assert isinstance(inter, MyInter)
                channel = inter.channel

                embed = Embed(
                    title="Vibr Is Restarting...",
                    description=(f"`ETA`: {eta}\n`Reason`: {reason}"),
                    color=Colour.greyple(),
                )
                embed.set_footer(
                    text="Playback *should* resume shortly after Vibr returns online."
                )

                await channel.send(embed=embed)

        await ctx.send(f"Closing with ETA of {eta} for {reason}")
        await self.bot.close()


def setup(bot: Vibr):
    bot.add_cog(Management(bot))
