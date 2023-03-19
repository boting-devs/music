from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord import StageChannel, VoiceChannel
from nextcord.ext.application_checks import check

from vibr.errors import NotConnected, NotInSameVoice

if TYPE_CHECKING:
    from botbase import MyInter


__all__ = ("is_connected",)


async def is_connected_predicate(inter: MyInter) -> bool:
    assert inter.guild is not None

    if not inter.guild.voice_client:
        raise NotConnected(inter.client)

    channel = inter.guild.voice_client.channel
    if not inter.user.voice or inter.user.voice.channel != channel:
        assert isinstance(channel, VoiceChannel | StageChannel)

        raise NotInSameVoice(channel)

    return True


is_connected = check(is_connected_predicate)  # pyright: ignore
