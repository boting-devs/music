from __future__ import annotations

from os import environ

from botbase import CogBase
from itsdangerous import URLSafeSerializer
from nextcord import slash_command
from ormar import NoMatch

from vibr.bot import Vibr
from vibr.db import User
from vibr.embed import Embed
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

    @spotify.subcommand(name="unlink")
    async def spotify_unlink(self, inter: Inter) -> None:
        """Unlink your spotify account."""

        try:
            user = await User.objects.get(id=inter.user.id)
        except NoMatch:
            embed = Embed(
                title="Not Linked", description="You are not linked to spotify."
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        if user.spotify_access_token is None:
            embed = Embed(
                title="Not Linked", description="You are not linked to spotify."
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        user.spotify_access_token = None
        user.spotify_refresh_token = None
        user.spotify_token_expires = None
        await user.update()

        embed = Embed(title="Unlinked", description="Your account has been unlinked.")
        await inter.send(embed=embed, ephemeral=True)


def setup(bot: Vibr) -> None:
    bot.add_cog(Spotify(bot))
