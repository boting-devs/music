from __future__ import annotations

from logging import getLogger
from traceback import format_exception

from botbase import CogBase, MyInter
from nextcord import ApplicationInvokeError

from vibr.bot import Vibr
from vibr.errors import CheckFailure

log = getLogger(__name__)


FORMAT = """command {command} gave
```py
{tb}
```
{channel} ({name}) in {guild} by {inter.user}
""".strip()


class ErrorHandler(CogBase[Vibr]):
    @CogBase.listener()
    async def on_application_command_error(
        self, inter: MyInter, exc: Exception
    ) -> None:
        if isinstance(exc, ApplicationInvokeError):
            exc = exc.original

        if isinstance(exc, CheckFailure):
            embed = exc.embed
            view = embed.view

            await inter.send(embed=embed, view=view, ephemeral=True)
        else:
            log.error(
                "Shit. Vibr just fookin died ༶ඬ༝ඬ༶ ᕙ(░ಥ╭͜ʖ╮ಥ░)━☆ﾟ.*･｡ﾟ ", exc_info=exc
            )
            if log_channel_id := self.bot.log_channel:
                log_channel = await self.bot.getch_channel(log_channel_id)

                command = (
                    inter.application_command.qualified_name
                    if inter.application_command
                    else ""
                )
                if inter.guild is None:
                    channel = "dm"
                    name = "dm"
                    guild = "dm"
                else:
                    channel = inter.channel.mention  # pyright: ignore
                    name = inter.channel.name  # pyright: ignore
                    guild = inter.guild.name

                tb = "\n".join(format_exception(exc))
                await log_channel.send_embed(
                    desc=FORMAT.format(
                        tb=tb,
                        channel=channel,
                        inter=inter,
                        name=name,
                        guild=guild,
                        command=command,
                    )
                )


def setup(bot: Vibr) -> None:
    bot.add_cog(ErrorHandler(bot))
