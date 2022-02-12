from __future__ import annotations

from logging import getLogger
from traceback import format_exception
from typing import TYPE_CHECKING

from botbase import MyContext
from nextcord import Color, Embed
from nextcord.ext.commands import (
    BotMissingPermissions,
    Cog,
    CommandInvokeError,
    CommandNotFound,
    MissingPermissions,
    NoPrivateMessage,
    NotOwner,
    PrivateMessageOnly,
)
from nextcord.utils import utcnow

from .extras.errors import NotInVoice, TooManyTracks, NotConnected
from .extras.views import LinkButtonView

if TYPE_CHECKING:
    from typing import Type

    from ..mmain import MyBot


log = getLogger(__name__)
eh: dict[Type[Exception], tuple[str, str]] = {
    NoPrivateMessage: ("Server Only", "This command can only be used in servers!"),
    PrivateMessageOnly: ("DMs Only", "This command can only be used in DMs!"),
    NotOwner: ("Owner Only", "This command can only be used by my owner!"),
    NotInVoice: ("Not in Voice", "You must be in a voice channel to use this command!"),
}


class Errors(Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.support_view = None
        self.bot.loop.create_task(self.init())

    async def init(self):
        await self.bot.wait_until_ready()
        self.support_view = LinkButtonView(
            name="Support Server",
            url="https://discord.gg/xck2R88Jv8",
            emoji="<:RobotPicture:919460440105431070>",
        )

    @staticmethod
    def format_embed(embed: Embed, ctx: MyContext) -> None:
        embed.timestamp = utcnow()
        embed.set_footer(
            text="report in the link below if this is weird |"
            f" do help {ctx.clean_prefix}{ctx.command} for info"
        )

    @Cog.listener()
    async def on_command_error(self, ctx: MyContext, error: Exception):
        assert self.support_view is not None
        if isinstance(error, CommandInvokeError):
            error = error.original

        if isinstance(error, CommandNotFound):
            return

        if (
            ctx.cog is not None
            and ctx.cog.qualified_name == "Jishaku"
            and not isinstance(error, NotOwner)
        ):
            embed = Embed(
                title="Error", description=f"```py\n{error}```", color=Color.red()
            )
            self.format_embed(embed, ctx)
            await ctx.send(embed=embed)
            return

        elif isinstance(error, NotConnected):
            if ctx.channel.permissions_for(ctx.me).add_reactions:  # type: ignore
                await ctx.message.add_reaction("\U0000274c")
            else:
                await ctx.send("I'm not even connected")

        elif isinstance(error, MissingPermissions):
            perms = ", ".join(
                f"`{p.replace('_', ' ').capitalize()}`"
                for p in error.missing_permissions
            )
            embed = Embed(
                title="Missing Permissions",
                description="You do not have permission to use this command. You need "
                f"{perms} permissions",
                color=self.bot.color,
            )
            self.format_embed(embed, ctx)
            await ctx.send(embed=embed, view=self.support_view)

        elif isinstance(error, BotMissingPermissions):
            perms = ", ".join(
                f"`{p.replace('_', ' ').capitalize()}`"
                for p in error.missing_permissions
            )
            embed = Embed(
                title="Missing Permissions",
                description="I do not have permission to use this command. I need "
                f"{perms} permissions",
                color=self.bot.color,
            )
            self.format_embed(embed, ctx)
            await ctx.send(embed=embed, view=self.support_view)

        elif type(error) in eh:
            embed = Embed(
                title=eh[type(error)][0],
                description=eh[type(error)][1],
                color=Color.red(),
            )
            self.format_embed(embed, ctx)
            await ctx.send(
                embed=embed,
                view=self.support_view,
            )

        else:
            embed = Embed(
                title="Unexpected Error.",
                description=f"```py\n{type(error).__name__}: {error}```my dev has been notified",
                color=Color.red(),
            )
            await ctx.send(embed=embed, view=self.support_view)
            painchannel = await self.bot.getch_channel(self.bot.logchannel)
            if ctx.guild is None:
                channel = "dm"
                name = "dm"
                guild = "dm"
            else:
                channel = ctx.channel.mention  # type: ignore
                name = ctx.channel.name  # type: ignore
                guild = ctx.guild.name
            tb = "\n".join(format_exception(type(error), error, error.__traceback__))
            await painchannel.send_embed(  # type: ignore
                desc=f"command {ctx.command} gave ```py\n{tb}```, "
                f"invoke: {ctx.message.content} in "
                f"{channel} ({name}) in {guild} by {ctx.author}"
            )
            log.error(
                "Command %s raised %s: %s",
                ctx.command,
                type(error).__name__,
                error,
                exc_info=True,
            )


def setup(bot: MyBot):
    bot.add_cog(Errors(bot))
