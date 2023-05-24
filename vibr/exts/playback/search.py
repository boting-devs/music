from __future__ import annotations

from botbase import CogBase
from mafic import Playlist, SearchType
from nextcord import SlashOption, slash_command

from vibr.bot import Vibr
from vibr.errors import NoTracksFound
from vibr.exts.liked._errors import NoPlaylists
from vibr.inter import Inter
from vibr.views import SearchView


class Search(CogBase[Vibr]):
    SEARCH_TYPE = SlashOption(
        name="search-type",
        choices={
            "Default": SearchType.YOUTUBE.value,
            "SoundCloud": SearchType.SOUNDCLOUD.value,
            "Spotify": SearchType.SPOTIFY_SEARCH.value,
            "Apple Music": SearchType.APPLE_MUSIC.value,
            "Deezer": SearchType.DEEZER_SEARCH.value,
            # "Yandex Music": SearchType.YANDEX_MUSIC.value,
        },
        default=SearchType.YOUTUBE.value,
    )

    @slash_command(dm_permission=False)
    async def search(
        self, inter: Inter, song: str, search_type: str = SEARCH_TYPE
    ) -> None:
        """Search for a song

        song:
            The song to search.

        search_type:
            The platform to search if this is a query."""

        await inter.response.defer(ephemeral=True)

        node = self.bot.pool.label_to_node["LOCAL"]
        result = await node.fetch_tracks(song, search_type=search_type or "youtube")

        if not result:
            raise NoTracksFound

        if isinstance(result, Playlist):
            raise NoPlaylists

        view = SearchView(result)
        embed = view.create_search_embed(tracks=result)
        await inter.send(embed=embed, view=view)
        view.message = inter

        await view.wait()

        track_index = view.selected_track
        track = result[track_index] if track_index is not None else None

        if track is None:
            return

        assert track.uri is not None

        await self.bot.play(inter=inter, query=track.uri)


def setup(bot: Vibr) -> None:
    bot.add_cog(Search(bot))
