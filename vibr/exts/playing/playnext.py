from __future__ import annotations

from botbase import CogBase
from mafic import Playlist, SearchType
from nextcord import slash_command 
from typing import TYPE_CHECKING
from logging import getLogger


from mafic import SearchType
from vibr.checks import is_connected
from vibr.bot import Vibr
from vibr.inter import Inter
from vibr.track_embed import track_embed
from vibr.utils import truncate

from ._errors import NoTracksFound

AUTOCOMPLETE_MAX = 25

if TYPE_CHECKING:
    from mafic import Track

log = getLogger(__name__)

def get_str(track: Track) -> str:
    return truncate(f"{track.title} by {track.author}", length=90)

class PlayNext(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    @is_connected
    async def playnext(self, inter:Inter,
        song: str
        ) -> None:
            """Play the song just after the current playing song
            song:Search song to be played next"""

            player = inter.guild.voice_client

            assert inter.guild is not None and inter.guild.voice_client is not None

            result = await player.fetch_tracks(query=song,search_type=SearchType.YOUTUBE.value)  # type: ignore
            if not result:
                raise NoTracksFound
            
            if isinstance(result,Playlist):
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
                await inter.send(embed=embed)

                if queued:
                    for i in tracks[::-1]:
                        player.queue.insert(0,i,inter.user.id)
            else:
                for i in tracks[::-1]:
                    player.queue.insert(0,i,inter.user.id)
                embed = await track_embed(
                    item, bot=self.bot, user=inter.user.id, playnext=True
                )
                await inter.send(embed=embed)

def setup(bot: Vibr) -> None:
    bot.add_cog(PlayNext(bot))