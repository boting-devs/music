from __future__ import annotations

from os import environ

from botbase import CogBase
from itsdangerous import URLSafeSerializer
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.inter import Inter


class Spotify(CogBase[Vibr]):
    AUTHORIZE_URL = f"{environ['SPOTIFY_REDIRECT_URL']}/spotify/authorize"

    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)

        self.serializer = URLSafeSerializer(
            secret_key=environ["OAUTH_SECRET_KEY"], salt="vibr"
        )

    @slash_command(dm_permission=False)
    async def spotify(self, inter: Inter) -> None:
        ...

    @spotify.subcommand(name="link")
    async def spotify_link(self, inter: Inter) -> None:
        """Link your spotify account."""

        signed_user_id = self.serializer.dumps(inter.user.id)
        await inter.send(f"{self.AUTHORIZE_URL}/?user={signed_user_id}")


def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))
