from __future__ import annotations


from botbase import CogBase
from nextcord import slash_command , ApplicationCommandType
from nextcord.utils import get

from vibr.bot import Vibr
from vibr.inter import Inter
from vibr.track_embed import track_embed

from mafic import SearchType ,Playlist

from ._errors import NoTracksFound


class Playnow(CogBase[Vibr]):
    async def playnow(self,inter:Inter,song:str) ->None:
        """Play the song immediately.
        song:The song to search, can be a link, a query, or a playlist.
        """
        if not inter.guild.voice_client:
            commands = self.bot.get_all_application_commands()
            join = get(commands, name="join", type=ApplicationCommandType.chat_input)
            if not join:
                raise RuntimeError

            await join(inter)

        await inter.response.defer()

        player = inter.guild.voice_client

        assert inter.guild is not None and inter.guild.voice_client is not None

        result = await player.fetch_tracks(
            query=song, search_type=SearchType.YOUTUBE.value
        ) # type: ignore

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
            await inter.followup.send(embed=embed)

            if queued:
                 player.queue += [(track, inter.user.id) for track in queued]

        else:
            for i in tracks[::-1]:
                player.queue.insert(0,i,inter.user.id)
                track , user = player.queue.skip(1)
                embed = await track_embed(
                    item, bot=self.bot, user=user,playnow=True
                )
                await inter.send(embed=embed)
                await player.play(track)

def setup(bot: Vibr) -> None:
    bot.add_cog(Playnow(bot))
