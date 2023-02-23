from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nextcord import Member, StageChannel, VoiceChannel
from nextcord.ext.application_checks import check

from vibr.embed import ErrorEmbed

from ._errors import AlreadyConnected

if TYPE_CHECKING:
    from botbase import MyInter


def already_connected_predicate(inter: MyInter) -> bool:
    if inter.guild and inter.guild.voice_client:
        raise AlreadyConnected(
            cast(StageChannel | VoiceChannel, inter.guild.voice_client.channel)
        )

    return True


already_connected = check(already_connected_predicate)  # pyright: ignore


async def can_connect(channel: VoiceChannel | StageChannel, *, inter: MyInter) -> bool:
    assert isinstance(inter.me, Member)

    if not channel.permissions_for(inter.me).connect:
        embed = ErrorEmbed(
            title="I Cannot Connect",
            description=f"I do not have permission to connect to {channel.mention}.",
        )
        await inter.response.send_message(embed=embed, view=embed.view)
        return False

    return True
