# pyright: reportGeneralTypeIssues=false

from __future__ import annotations

from typing import TYPE_CHECKING

from async_spotify.authentification import SpotifyAuthorisationToken
from botbase import BaseMeta
from ormar import BigInteger, DateTime, Model, String

if TYPE_CHECKING:
    from datetime import datetime


class User(Model):
    class Meta(BaseMeta):
        tablename = "users"

    id: int = BigInteger(primary_key=True, autoincrement=False)
    spotify_access_token: str | None = String(max_length=255, nullable=True)
    spotify_refresh_token: str | None = String(max_length=255, nullable=True)
    spotify_activation_time: datetime | None = DateTime(timezone=True, nullable=True)

    @property
    def spotify(self) -> SpotifyAuthorisationToken | None:
        if (
            self.spotify_access_token is None
            or self.spotify_refresh_token is None
            or self.spotify_activation_time is None
        ):
            return None

        return SpotifyAuthorisationToken(
            access_token=self.spotify_access_token,
            refresh_token=self.spotify_refresh_token,
            activation_time=self.spotify_activation_time.timestamp(),
        )
