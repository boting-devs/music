from __future__ import annotations

from typing import cast

from nextcord import Member, StageChannel, VoiceChannel
from nextcord.ext.application_checks import check

from vibr.embed import ErrorEmbed
from vibr.inter import Inter

from ._errors import AlreadyConnected


def already_connected_predicate(inter: Inter) -> bool:
    if inter.guild and inter.guild.voice_client:
        raise AlreadyConnected(
            cast(StageChannel | VoiceChannel, inter.guild.voice_client.channel)
        )

    return True


already_connected = check(already_connected_predicate)  # pyright: ignore


async def can_connect(channel: VoiceChannel | StageChannel, *, inter: Inter) -> bool:
    assert isinstance(inter.me, Member)

    if not channel.permissions_for(inter.me).connect:
        embed = ErrorEmbed(
            title="I Cannot Connect",
            description=f"I do not have permission to connect to {channel.mention}.",
        )
        await inter.send(embed=embed, view=embed.view, ephemeral=True)
        return False

    if channel.user_limit and len(channel.voice_states) >= channel.user_limit:
        permissions = channel.permissions_for(channel.guild.me)
        if not (permissions.move_members or permissions.administrator):
            embed = ErrorEmbed(
                title="I Cannot Connect",
                description=f"{channel.mention} is full, "
                "and I do not have permission to move members.",
            )
            await inter.send(embed=embed, view=embed.view, ephemeral=True)
            return False

    return True
