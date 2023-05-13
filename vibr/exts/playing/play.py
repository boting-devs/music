from __future__ import annotations

from botbase import CogBase
from mafic import Playlist, SearchType
from nextcord import ApplicationCommandType, SlashOption, slash_command
from nextcord.utils import get

from vibr.bot import Vibr
from vibr.inter import Inter
from vibr.track_embed import track_embed

from ._errors import NoTracksFound


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

    @slash_command(dm_permission=False)
    async def play(
        self, inter: Inter, query: str, search_type: str = SEARCH_TYPE,
        type: int = SlashOption(name="type",choices={"next":69 , "now":420},default=None)
    ) -> None:
        """Play a link, query or past song.

        query:
            Can be a URL/link, query or past played song.
        search_type:
            The platform to search if this is a query.
        """

        if not inter.guild.voice_client:
            commands = self.bot.get_all_application_commands()
            join = get(commands, name="join", type=ApplicationCommandType.chat_input)
            if not join:
                raise RuntimeError

            await join(inter)
        else:
            await inter.response.defer()

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

            embed = await track_embed(item,bot=self.bot,user=inter.user.id)
            await inter.followup.send(embed=embed)

            if queued:
                if type == 69:
                    for i in tracks[::-1]:
                        player.queue.insert(0, i, inter.user.id)

                else:
                    player.queue += [(track, inter.user.id) for track in queued]
        else:
            if type ==69:
                for i in tracks[::-1]:
                    player.queue.insert(0, i, inter.user.id)
                embed = await track_embed(
                    item, bot=self.bot, user=inter.user.id, playnext=True
                )
                await inter.send(embed=embed)

            elif type == 420:
                for i in tracks[::-1]:
                    player.queue.insert(0, i, inter.user.id)
                track, user = player.queue.skip(1)
                embed = await track_embed(item, bot=self.bot, user=user, playnow=True)
                await inter.send(embed=embed)
                await player.play(track)


            elif type ==None:
                player.queue += [(track, inter.user.id) for track in tracks]
                l=len(player.queue)
                embed = await track_embed(
                    item, bot=self.bot, user=inter.user.id, queued=True,index=l
                )
                await inter.followup.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Play(bot))
