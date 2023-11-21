from __future__ import annotations

from datetime import timedelta
from os import getenv
from typing import TYPE_CHECKING

from nextcord import StageChannel, VoiceChannel
from nextcord.ext.application_checks import check
from nextcord.utils import utcnow

from vibr.errors import (
    CommandUnderMaintainance,
    NotConnected,
    NotInSameVoice,
    NotPlaying,
    NotVoted,
)

if TYPE_CHECKING:
    from vibr.inter import Inter

__all__ = ("is_connected", "is_connected_and_playing", "voted")
VOTE_INTERVAL = timedelta(hours=24)
VOTING = bool(getenv("TOPGG_VOTING"))


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


async def voted_predicate(inter: Inter) -> bool:
    if not VOTING:
        return True

    return True

    user = await User.select(User.topgg_voted).where(User.id == inter.user.id).first()
    if user is None:
        raise NotVoted(inter.client)

    vote_time = user["topgg_voted"]

    if vote_time is None or (vote_time + VOTE_INTERVAL) < utcnow():
        raise NotVoted(inter.client)

    return True


is_connected = check(is_connected_predicate)  # pyright: ignore[reportGeneralTypeIssues]
is_connected_and_playing = check(
    is_connected_and_playing_predicate  # pyright: ignore[reportGeneralTypeIssues]
)
voted = check(voted_predicate)  # pyright: ignore[reportGeneralTypeIssues]


async def maintainance_predicate(_: Inter) -> bool:
    raise CommandUnderMaintainance


maintainance = check(maintainance_predicate)  # pyright: ignore[reportGeneralTypeIssues]
