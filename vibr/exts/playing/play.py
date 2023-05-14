from __future__ import annotations

from typing import TYPE_CHECKING

from botbase import CogBase
from mafic import Playlist, SearchType, Track
from nextcord import ApplicationCommandType, SlashOption, slash_command
from nextcord.utils import get

from vibr.bot import Vibr
from vibr.inter import Inter
from vibr.track_embed import track_embed

from ._errors import NoTracksFound

if TYPE_CHECKING:
    from vibr.player import Player


class Play(CogBase[Vibr]):
    SEARCH_TYPE = SlashOption(
        name="search-type",
        choices={
            "Default": SearchType.YOUTUBE.value,
            "SoundCloud": SearchType.SOUNDCLOUD.value,
            "Spotify": SearchType.SPOTIFY_SEARCH.value,
            "Apple Music": SearchType.APPLE_MUSIC.value,
            "Deezer": SearchType.DEEZER_SEARCH.value,
            "Yandex Music": SearchType.YANDEX_MUSIC.value,
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
        type: str = TYPE,
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

        await self.assert_player(inter=inter)
        player = inter.guild.voice_client
        player.notification_channel = inter.channel  # pyright: ignore

        result = await player.fetch_tracks(
            query=query, search_type=SearchType(search_type)
        )
        if not result:
            raise NoTracksFound

        if isinstance(result, Playlist):
            tracks = result.tracks
            item = result
            track = tracks[0]
        else:
            item = track = result[0]
            tracks = [track]

        if player.current is None:
            queued = tracks[1:]
            await player.play(track)

            embed = await track_embed(item, bot=self.bot, user=inter.user.id)

            if queued:
                if type == "Next":
                    for i in tracks[::-1]:
                        player.queue.insert(0, i, inter.user.id)
                else:
                    player.queue += [(track, inter.user.id) for track in queued]
        elif type == "Next":
            await self.handle_play_next(
                player=player, inter=inter, item=item, tracks=tracks
            )
        elif type == "Now":
            await self.handle_play_now(
                player=player, inter=inter, item=item, tracks=tracks
            )
        else:
            player.queue += [(track, inter.user.id) for track in tracks]
            length = len(player.queue)
            embed = await track_embed(
                item, bot=self.bot, user=inter.user.id, queued=length
            )

        await inter.channel.send(embed=embed)  # pyright: ignore

    async def handle_play_now(
        self,
        *,
        player: Player,
        inter: Inter,
        item: Track | Playlist,
        tracks: list[Track],
    ) -> None:
        for i in tracks[::-1]:
            player.queue.insert(0, i, inter.user.id)
        track, user = player.queue.skip(1)
        await track_embed(item, bot=self.bot, user=user)
        await player.play(track)

    async def handle_play_next(
        self,
        *,
        player: Player,
        inter: Inter,
        item: Track | Playlist,
        tracks: list[Track],
    ) -> None:
        for i in tracks[::-1]:
            player.queue.insert(0, i, inter.user.id)
        await track_embed(item, bot=self.bot, user=inter.user.id, queued=1)

    async def assert_player(self, *, inter: Inter) -> None:
        if not inter.guild.voice_client:
            commands = self.bot.get_all_application_commands()
            join = get(commands, name="join", type=ApplicationCommandType.chat_input)
            if not join:
                raise RuntimeError

            await join(inter)
        else:
            await inter.response.defer()


def setup(bot: Vibr) -> None:
    bot.add_cog(Play(bot))
