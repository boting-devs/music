from __future__ import annotations

from botbase import CogBase
from nextcord import slash_command

from vibr.bot import Vibr
from vibr.checks import is_connected_and_playing
from vibr.embed import Embed
from vibr.inter import Inter


class LoopCommand(CogBase[Vibr]):
    @slash_command(dm_permission=False)
    async def loop(self, inter: Inter) -> None:
        ...

    @loop.subcommand(name="track")
    @is_connected_and_playing
    async def loop_track(self, inter: Inter) -> None:
        """Loop the currently playing track."""
        player = inter.guild.voice_client
        assert player.current is not None

        if not player.queue.loop_type:
            player.queue.loop_track(player.current, user=inter.user.id)
            embed = Embed(title="Looping Current Track")
        elif player.queue.loop_type:
            player.queue.loop_track(player.current, user=inter.user.id)
            embed = Embed(title="Switching Loop Type to Track")
        else:
            player.queue.disable_loop()
            embed = Embed(title="Track Looping Disabled")

        await inter.send(embed=embed)

    @loop.subcommand(name="queue")
    @is_connected_and_playing
    async def loop_queue(self, inter: Inter) -> None:
        """Loop the whole queue."""

        player = inter.guild.voice_client
        assert player.current is not None

        if not player.queue.loop_type:
            player.queue.loop_queue(current=player.current, user=inter.user.id)
            embed = Embed(title="Looping Queue")
        elif player.queue.loop_type:
            player.queue.loop_queue(current=player.current, user=inter.user.id)
            embed = Embed(title="Switching Loop Type to Queue")
        else:
            player.queue.disable_loop()
            embed = Embed(title="Queue Looping Disabled")

        await inter.send(embed=embed)


def setup(bot: Vibr) -> None:
    bot.add_cog(LoopCommand(bot))
