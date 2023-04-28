from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord import StageChannel, VoiceChannel
from nextcord.ext.application_checks import check

from vibr.errors import NotConnected, NotInSameVoice, NotPlaying

if TYPE_CHECKING:
    from vibr.inter import Inter

__all__ = ("is_connected", "is_connected_and_playing")


async def is_connected_predicate(inter: Inter) -> bool:
    if not inter.guild.voice_client:
        raise NotConnected(inter.client)

    channel = inter.guild.voice_client.channel
    if not inter.user.voice or inter.user.voice.channel != channel:
        assert isinstance(channel, VoiceChannel | StageChannel)

        raise NotInSameVoice(channel)

    return True


async def is_connected_and_playing_predicate(inter: Inter) -> bool:
    player = inter.guild.voice_client

    if not inter.guild.voice_client:
        raise NotConnected(inter.client)

    channel = inter.guild.voice_client.channel
    if not inter.user.voice or inter.user.voice.channel != channel:
        assert isinstance(channel, VoiceChannel | StageChannel)

        raise NotInSameVoice(channel)

    if player.current is None:
        raise NotPlaying(inter.client)

    return True


is_connected = check(is_connected_predicate)  # pyright: ignore
is_connected_and_playing = check(is_connected_and_playing_predicate)  # pyright: ignore
