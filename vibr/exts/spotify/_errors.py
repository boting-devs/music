from vibr.bot import Vibr
from vibr.embed import ErrorEmbed
from vibr.errors import CheckFailure

__all__ = ("NotLinked",)


class NotLinked(CheckFailure):
    def __init__(self, bot: Vibr) -> None:
        self.embed = ErrorEmbed(
            title="Not Linked to Spotify",
            description=(
                f"Use {bot.get_command_mention('spotify link')} to link your account!"
            ),
        )


class InvalidSpotifyUrl(CheckFailure):
    URL_HELP = "https://cdn.discordapp.com/attachments/802586580766162967/1108776366154977402/KSzS.png"

    embed = ErrorEmbed(
        title="Invalid Profile URL",
        description="That is not a valid profile url. See below for details.",
    )
    embed.set_image(url=URL_HELP)
