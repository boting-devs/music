from __future__ import annotations

from botbase import CogBase
from mafic import Filter, Rotation
from nextcord import Range, slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter


class Rotate(CogBase[Vibr]):
    @slash_command(name="rotate", dm_permission=False)
    @is_connected_and_playing
    async def rotate(
        self, inter: Inter, frequency: Range[0.1, 10] | None  # pyright: ignore
    ) -> None:
        """A cool filter to pan audio around your head,
        best with headphones or other stereo audio systems!

        frequency:
            The frequency in Hz (times/second) to pan audio.
            The best values are below 1, >5 is trippy.
        """

        passed_custom = frequency is not None

        frequency = frequency or 0.2  # pyright: ignore

        player = inter.guild.voice_client

        if await player.has_filter("rotate") and passed_custom:
            await player.remove_filter("rotate")
            rotate = Rotation(rotation_hz=frequency)  # pyright: ignore
            rotate_filter = Filter(rotation=rotate)
            await player.add_filter(rotate_filter, label="rotate", fast_apply=True)
            embed = Embed(title="Rotation filter modified")
        elif await player.has_filter("rotate"):
            await player.remove_filter("rotate", fast_apply=True)
            embed = Embed(title="Rotation filter Deactivated")
        else:
            rotate = Rotation(rotation_hz=frequency)  # pyright: ignore
            rotate_filter = Filter(rotation=rotate)
            await player.add_filter(rotate_filter, label="rotate", fast_apply=True)
            embed = Embed(title="Rotation filter activated")

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(Rotate(bot))