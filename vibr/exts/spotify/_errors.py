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
