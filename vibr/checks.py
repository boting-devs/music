from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord import StageChannel, VoiceChannel
from nextcord.ext.application_checks import check

from vibr.errors import NotConnected, NotInSameVoice, NotPlaying

if TYPE_CHECKING:
    from botbase import MyInter

    from vibr.player import Player


__all__ = ("is_connected","is_connected_and_playing")


async def is_connected_predicate(inter: MyInter) -> bool:
    assert inter.guild is not None

    if not inter.guild.voice_client:
        raise NotConnected(inter.client)

    channel = inter.guild.voice_client.channel
    if not inter.user.voice or inter.user.voice.channel != channel:
        assert isinstance(channel, VoiceChannel | StageChannel)

        raise NotInSameVoice(channel)

    return True


async def is_connected_and_playing_predicate(inter:MyInter) -> bool:
    assert inter.guild is not None
    player: Player = inter.guild.voice_client  # pyright: ignore

    if not inter.guild.voice_client:
        raise NotConnected(inter.client)

    channel = inter.guild.voice_client.channel
    if not inter.user.voice or inter.user.voice.channel != channel:
        assert isinstance(channel, VoiceChannel | StageChannel)

        raise NotInSameVoice(channel)

    if player.current is None:
        raise NotPlaying


    return True


is_connected = check(is_connected_predicate)  # pyright: ignore
is_connected_and_playing = check(is_connected_and_playing_predicate) #pyright: ignore
