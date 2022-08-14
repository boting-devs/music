from __future__ import annotations

from logging import getLogger
from traceback import format_exception
from typing import TYPE_CHECKING

from botbase import MyContext, MyInter
from nextcord import ApplicationInvokeError, Color, Embed
from nextcord.ext.application_checks import (
    ApplicationBotMissingPermissions as ABotMissingPermissions,
)
from nextcord.ext.application_checks import (
    ApplicationMissingPermissions as AMissingPermissions,
)
from nextcord.ext.commands import (
    BotMissingPermissions,
    Cog,
    CommandInvokeError,
    CommandNotFound,
    MissingPermissions,
    MissingRequiredArgument,
    NoPrivateMessage,
    NotOwner,
    PrivateMessageOnly,
)
from nextcord.utils import utcnow
from pomice.exceptions import NoNodesAvailable, TrackLoadError

from .extras.errors import (
    LyricsNotFound,
    NotConnected,
    NotInSameVoice,
    NotInVoice,
    SongNotProvided,
    TooManyTracks,
)
from .extras.views import LinkButtonView

if TYPE_CHECKING:
    from typing import Type

    from ..__main__ import Vibr


log = getLogger(__name__)
ehh: dict[Type[Exception], tuple[str, str]] = {
    NoPrivateMessage: ("Server Only", "This command can only be used in servers!"),
    PrivateMessageOnly: ("DMs Only", "This command can only be used in DMs!"),
    NotOwner: ("Owner Only", "This command can only be used by my owner!"),
    NotInVoice: ("Not in Voice", "You must be in a voice channel to use this command!"),
    TooManyTracks: (
        "Too Many Tracks",
        "You can only queue up to 100 tracks at a time!",
    ),
    LyricsNotFound: (
        "No Lyrics Found",
        "Sorry, could not find lyrics for that track :(",
    ),
    NotInSameVoice: (
        "Not in same voice channel",
        "You need to be in same voice channel same as bot",
    ),
    SongNotProvided: ("No Song Provided", "Please provide a song to search for lyrics"),
    NotConnected: (
        "Not Connected",
        "This command requires the bot to be connected to a vc",
    ),
    NoNodesAvailable: (
        "There was an issue playing this song",
        "This was not a user error, the bot may have recently rebooted. Please try again in a few seconds.",
    ),
}
eh: dict[str, tuple[str, str]] = {e.__name__: msg for e, msg in ehh.items()}


class Errors(Cog):
    def __init__(self, bot: Vibr):
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
    def format_embed(embed: Embed, ctx: MyContext | MyInter) -> None:
        embed.timestamp = utcnow()
        embed.set_footer(
            text="report in the link below if this is weird |"
            f" do {ctx.clean_prefix}help {ctx.command} for info"
        )

    @Cog.listener()
    async def on_application_command_error(self, inter: MyInter, error: Exception):
        await self.on_command_error(inter, error)

    @Cog.listener()
    async def on_command_error(self, ctx: MyContext | MyInter, error: Exception):
        if isinstance(error, (CommandInvokeError, ApplicationInvokeError)):
            error = error.original

        if isinstance(error, CommandNotFound):
            return

        if (
            (cog := getattr(ctx, "cog", None))
            and cog.qualified_name == "Jishaku"
            and not isinstance(error, NotOwner)
        ):
            embed = Embed(
                title="Error", description=f"```py\n{error}```", color=Color.red()
            )
            self.format_embed(embed, ctx)
            await ctx.send(embed=embed)
            return

        elif isinstance(error, NotConnected):
            if ctx.channel.permissions_for(ctx.me).add_reactions and isinstance(ctx, MyContext):  # type: ignore
                await ctx.message.add_reaction("\U0000274c")
            else:
                await ctx.send("I'm not even connected")

        elif isinstance(error, (MissingPermissions, AMissingPermissions)):
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

        elif isinstance(error, (BotMissingPermissions, ABotMissingPermissions)):
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

        elif isinstance(error, MissingRequiredArgument):
            embed = Embed(
                title="Missing Argument",
                description=error,
                color=self.bot.color,
            )
            self.format_embed(embed, ctx)
            await ctx.send(embed=embed, view=self.support_view)

        elif isinstance(error, TrackLoadError):
            embed = Embed(
                title="An error occured",
                description=f"**{error}**",
                color=self.bot.color,
            )
            self.format_embed(embed, ctx)
            await ctx.send(embed=embed, view=self.support_view)

        elif type(error).__name__.lstrip("Application") in eh:
            name = type(error).__name__.lstrip("Application")

            embed = Embed(
                title=eh[name][0],
                description=eh[name][1],
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
            if self.bot.logchannel is not None:
                painchannel = await self.bot.getch_channel(self.bot.logchannel)
                content = (
                    ctx.message.content
                    if isinstance(ctx, MyContext)
                    else ctx.data and ctx.data.get("name")
                )
                if ctx.guild is None:
                    channel = "dm"
                    name = "dm"
                    guild = "dm"
                else:
                    channel = ctx.channel.mention  # type: ignore
                    name = ctx.channel.name  # type: ignore
                    guild = ctx.guild.name
                tb = "\n".join(
                    format_exception(type(error), error, error.__traceback__)
                )
                await painchannel.send_embed(  # type: ignore
                    desc=f"command {ctx.command} gave ```py\n{tb}```, "
                    f"invoke: {content} in "
                    f"{channel} ({name}) in {guild} by {ctx.author}"
                )
                log.error(
                    "Command %s raised %s: %s",
                    ctx.command,
                    type(error).__name__,
                    error,
                    exc_info=True,
                )


def setup(bot: Vibr):
    bot.add_cog(Errors(bot))
