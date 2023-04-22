from __future__ import annotations

from typing import TYPE_CHECKING ,Optional

from botbase import CogBase, MyInter
from mafic.filter import Rotation
from nextcord import slash_command ,Range

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed

if TYPE_CHECKING:
    from vibr.player import Player

class Rotate(CogBase[Vibr]):
    @slash_command(name="rotate",dm_permission=False)
    @is_connected_and_playing
    async def rotate(self,inter:MyInter,frequency: Optional[Range[0.1,10]]) -> None:
        """A cool filter to pan audio around your head,
        best with headphones or other stereo audio systems!

        frequency:
            The frequency in Hz (times/second) to pan audio.
            The best values are below 1, >5 is trippy."
        """

        passed_custom = frequency is not None

        frequency = frequency or 0.2 

        assert inter.guild is not None and inter.guild.voice_client is not None

        player: Player = inter.guild.voice_client  # pyright: ignore

        if await player.has_filter("rotate") and passed_custom:
            await player.remove_filter("rotate")
            await player.add_filter(
                Rotation(rotation_hz=frequency),label="rotate",fast_apply=True
            )
            embed = Embed("Rotation filter modified")

        elif await player.has_filter("rotate"):
            await player.remove_filter("rotate",fast_apply=True)
            await inter.send("Rotation filter Deactivated")

        else:
            await player.add_filter(
                Rotation(rotation_hz=frequency),label="rotate",fast_apply=True
            )
            await inter.send("Rotation filter activated")

def setup(bot: Vibr) -> None:
    bot.add_cog(Rotate(bot))