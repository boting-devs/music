from __future__ import annotations

from botbase import CogBase
from mafic import Playlist, SearchType
from nextcord import SlashOption, slash_command

from vibr.bot import Vibr
from vibr.database import add_to_liked
from vibr.errors import NoTracksFound
from vibr.inter import Inter
from vibr.views import SearchView

from ._errors import *


class Liked(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    async def liked(self, inter: Inter) -> None:
        ...

    SEARCH_TYPE = SlashOption(
        name="search-type",
        choices={
            "Default": SearchType.YOUTUBE.value,
            "SoundCloud": SearchType.SOUNDCLOUD.value,
            "Spotify": SearchType.SPOTIFY_SEARCH.value,
            "Apple Music": SearchType.APPLE_MUSIC.value,
            "Deezer": SearchType.DEEZER_SEARCH.value,
        },
        default=SearchType.YOUTUBE.value,
    )

    @liked.subcommand(name="add")
    async def liked_add(
        self,
        inter: Inter,
        query: str | None = None,
        search_type: str | None = SEARCH_TYPE,
    ) -> None:
        """Add a song to your liked songs playlist.

        query:
            Can be a URL/link, query or past played song.
            Leave blank to use the currently playing song.
        search_type:
            The platform to search if this is a query.
        """

        await inter.response.defer(ephemeral=True)

        track = inter.guild.voice_client and inter.guild.voice_client.current

        if query:
            player = inter.guild.voice_client
            result = await player.fetch_tracks(
                query, search_type=SearchType(search_type)
            )

            if not result:
                raise NoTracksFound

            if isinstance(result, Playlist):
                raise NoPlaylists

            view = SearchView(result)
            embed = view.create_search_embed(tracks=result)
            message = await inter.edit_original_message(embed=embed, view=view)
            view.message = message

            await view.wait()

            track = view.selected_track

            if track is None:
                return

        elif track is None:
            raise NoTrackOrQuery

        await add_to_liked(user=inter.author, track=track)

        await inter.send(
            f"Added **{track.title}** to your liked songs playlist.",
            ephemeral=True,
        )


def setup(bot: Vibr) -> None:
    bot.add_cog(Liked(bot))
