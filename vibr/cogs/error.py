from __future__ import annotations

from logging import getLogger
from traceback import format_exception
from typing import TYPE_CHECKING

from botbase import MyContext, MyInter
from nextcord import ApplicationInvokeError, Color, Embed
from nextcord.ext.application_checks import (
    ApplicationBotMissingPermissions as BotMissingPermissions,
)
from nextcord.ext.application_checks import (
    ApplicationMissingPermissions as MissingPermissions,
)
from nextcord.ext.commands import Cog, CommandNotFound, NotOwner
from nextcord.utils import MISSING, utcnow
from pomice.exceptions import NoNodesAvailable, TrackInvalidPosition, TrackLoadError
from pomice.spotify.exceptions import SpotifyRequestException

from .extras.errors import (
    Ignore,
    LyricsNotFound,
    NotConnected,
    NotInSameVoice,
    NotInVoice,
    NotPlaying,
    SongNotProvided,
    TooManyTracks,
    VoteRequired,
)
from .extras.views import LinkButtonView

if TYPE_CHECKING:
    from typing import Type

    from ..__main__ import Vibr


log = getLogger(__name__)
errors: dict[Type[Exception], tuple[str, str]] = {
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
    VoteRequired: (
        "This command requires a vote",
        "Please vote for the bot [here](https://top.gg/bot/882491278581977179/vote) to use this command",
    ),
    NotPlaying: (
        "Please Play A Song",
        "To use this command, play a song using </play:987418268635639848>",
    ),
}
e: dict[str, tuple[str, str]] = {k.__name__: v for k, v in errors.items()}


class Errors(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot
        self.support_view = MISSING
        # The bot needs to be ready, make a background task to create `support_view`
        self.bot.loop.create_task(self.init())

    async def init(self):
        await self.bot.wait_until_ready()
        self.support_view = LinkButtonView(
            name="Support Server",
            url="https://discord.gg/GHKuu8gTT6",
            emoji="<:RobotPicture:919460440105431070>",
        )

    @staticmethod
    def format_embed(embed: Embed) -> None:
        embed.timestamp = utcnow()
        embed.set_footer(text="report in the link below if this is weird")

    @Cog.listener()
    async def on_command_error(self, ctx: MyContext, error: Exception):
        if not isinstance(error, (NotOwner, CommandNotFound)):
            embed = Embed(
                title="Error", description=f"```py\n{error}```", color=Color.red()
            )
            self.format_embed(embed)
            await ctx.send(embed=embed)
            log.error(
                "Command %s raised %s: %s",
                ctx.command,
                type(error).__name__,
                error,
                exc_info=True,
            )

    @Cog.listener()
    async def on_application_command_error(self, inter: MyInter, error: Exception):
        if isinstance(error, ApplicationInvokeError):
            error = error.original

        if isinstance(error, Ignore):
            return

        elif isinstance(error, NotConnected):
            await inter.send("I'm not even connected")

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
            self.format_embed(embed)
            await inter.send(embed=embed, view=self.support_view, ephemeral=True)

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
            self.format_embed(embed)
            await inter.send(embed=embed, view=self.support_view, ephemeral=True)

        elif isinstance(error, TrackLoadError):
            embed = Embed(
                title="An Error Occured When Loading Your Track",
                description=f"**{error}**",
                color=self.bot.color,
            )
            self.format_embed(embed)
            await inter.send(embed=embed, view=self.support_view, ephemeral=True)

        elif isinstance(error, TrackInvalidPosition):
            embed = Embed(
                title="Invalid Track Position",
                description="Seek position must be between 0 and the track length",
                color=self.bot.color,
            )
            self.format_embed(embed)
            await inter.send(embed=embed, view=self.support_view, ephemeral=True)

        elif isinstance(error, SpotifyRequestException):
            embed = Embed(
                title="An Error Occurred When Playing From Spotify",
                description=str(error),
                color=self.bot.color,
            )
            self.format_embed(embed)
            await inter.send(embed=embed, view=self.support_view, ephemeral=True)

        elif type(error).__name__ in e:
            title, description = e[type(error).__name__]

            embed = Embed(
                title=title,
                description=description,
                color=Color.red(),
            )
            self.format_embed(embed)
            await inter.send(embed=embed, view=self.support_view, ephemeral=True)

        else:
            embed = Embed(
                title="Unexpected Error.",
                description=(
                    f"```py\n{type(error).__name__}: {error}```my dev has been notified\n"
                    "**This is not a user error, retrying likely will not work.**"
                ),
                color=Color.red(),
            )
            await inter.send(embed=embed, view=self.support_view, ephemeral=True)
            if self.bot.logchannel is not None:
                painchannel = await self.bot.getch_channel(self.bot.logchannel)
                content = inter.application_command.qualified_name  # type: ignore
                if inter.guild is None:
                    channel = "dm"
                    name = "dm"
                    guild = "dm"
                else:
                    channel = inter.channel.mention  # type: ignore
                    name = inter.channel.name  # type: ignore
                    guild = inter.guild.name
                tb = "\n".join(
                    format_exception(type(error), error, error.__traceback__)
                )
                await painchannel.send_embed(  # type: ignore
                    desc=f"command {inter.command} gave ```py\n{tb}```, "
                    f"invoke: {content} in "
                    f"{channel} ({name}) in {guild} by {inter.user}"
                )
                log.error(
                    "Command %s raised %s: %s",
                    inter.command,
                    type(error).__name__,
                    error,
                    exc_info=True,
                )


def setup(bot: Vibr):
    bot.add_cog(Errors(bot))
