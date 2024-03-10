from __future__ import annotations

from botbase import CogBase
from mafic import SearchType
from nextcord import SlashOption, slash_command

from vibr.bot import Vibr
from vibr.inter import Inter


class Play(CogBase[Vibr]):
    SEARCH_TYPE = SlashOption(
        name="source",
        choices={
            "Default": SearchType.SPOTIFY_SEARCH.value,
            "SoundCloud": SearchType.SOUNDCLOUD.value,
            "Spotify": SearchType.YOUTUBE_MUSIC.value,
            "Apple Music": SearchType.APPLE_MUSIC.value,
            "Deezer": SearchType.DEEZER_SEARCH.value,
            # "Yandex Music": SearchType.YANDEX_MUSIC.value,
        },
        default=SearchType.YOUTUBE.value,
    )
    TYPE = SlashOption(choices=["Next", "Now"], default=None)

    @slash_command(dm_permission=False)
    async def play(
        self,
        inter: Inter,
        query: str,
        search_type: str = SEARCH_TYPE,
        type: str | None = TYPE,
    ) -> None:
        """Play a link, query or past song.

        query:
            Can be a URL/link, query or past played song.
        search_type:
            The platform to search if this is a query.
        type:
            When to play this track. Leave blank to queue if something is already
            playing.
        """

        await self.bot.play(
            inter=inter, query=query, search_type=search_type, type=type
        )


def setup(bot: Vibr) -> None:
    bot.add_cog(Play(bot))
