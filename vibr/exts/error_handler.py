from __future__ import annotations

from contextlib import suppress
from logging import getLogger
from traceback import format_exception

from botbase import CogBase
from mafic import NoNodesAvailable, PlayerNotConnected, TrackLoadException
from nextcord import ApplicationInvokeError, Colour, NotFound
from prometheus_client import Counter

from vibr.bot import Vibr
from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure
from vibr.inter import Inter

log = getLogger(__name__)


FORMAT = """command {command} gave
```py
{tb}
```
{channel} in {guild} by {inter.user}
""".strip()
UNKNOWN_INTERACTION = 10062


class ErrorHandler(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)
        self.unhandled_error_count = Counter(
            "vibr_unhandled_errors", "Unhandled errors"
        )

    @CogBase.listener()
    async def on_application_command_error(self, inter: Inter, exc: Exception) -> None:
        if isinstance(exc, ApplicationInvokeError):
            exc = exc.original

        if isinstance(exc, CheckFailure):
            embed = exc.embed
            view = exc.view if exc.view else embed.view

            await inter.send(embed=embed, view=view, ephemeral=True)
        elif isinstance(exc, TrackLoadException):
            embed = ErrorEmbed(title="Failed to load track", description=exc.message)
            await inter.send(embed=embed, view=embed.view, ephemeral=True)
        elif isinstance(exc, NoNodesAvailable):
            embed = ErrorEmbed(
                title="Wait", description="The bot is still restarting..."
            )
            await inter.send(embed=embed, view=embed.view, ephemeral=True)
        elif isinstance(exc, PlayerNotConnected):
            embed = ErrorEmbed(
                title="Something went wrong",
                description="Try connecting again.",
            )
            if inter.guild is not None and inter.guild.voice_client is not None:
                await inter.guild.voice_client.disconnect(force=True)
            await inter.send(embed=embed, view=embed.view, ephemeral=True)
        elif isinstance(exc, NotFound) and exc.code == UNKNOWN_INTERACTION:
            return
        else:
            self.unhandled_error_count.inc()
            log.error(
                "Unexpected error in command %s",
                inter.application_command.qualified_name
                if inter.application_command
                else None,
                exc_info=exc,
            )
            embed = ErrorEmbed(
                title="Unexpected Error.",
                description=(
                    f"```py\n{type(exc).__name__}: {exc}```\n"
                    "Developers have been notified.\n"
                    "**This is not a user error, retrying likely will not work.**"
                ),
                color=Colour.red(),
            )
            with suppress(NotFound):
                await inter.send(embed=embed, view=embed.view, ephemeral=True)

            if log_channel_id := self.bot.log_channel:
                log_channel = await self.bot.getch_channel(log_channel_id)

                command = (
                    inter.application_command.qualified_name
                    if inter.application_command
                    else ""
                )
                if inter.guild is None:
                    channel = "dm"
                    guild = "dm"
                else:
                    channel = inter.channel.mention  # pyright: ignore  # noqa: PGH003
                    guild = inter.guild.name

                tb = "\n".join(format_exception(exc))
                await log_channel.send_embed(
                    desc=FORMAT.format(
                        tb=tb,
                        channel=channel,
                        inter=inter,
                        guild=guild,
                        command=command,
                    )
                )


def setup(bot: Vibr) -> None:
    bot.add_cog(ErrorHandler(bot))
