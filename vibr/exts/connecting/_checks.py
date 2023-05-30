from __future__ import annotations

from typing import cast

from nextcord import StageChannel, VoiceChannel
from nextcord.ext.application_checks import check

from vibr.inter import Inter

from ._errors import AlreadyConnected


def already_connected_predicate(inter: Inter) -> bool:
    if inter.guild and inter.guild.voice_client:
        raise AlreadyConnected(
            cast(StageChannel | VoiceChannel, inter.guild.voice_client.channel)
        )

    return True


already_connected = check(
    already_connected_predicate  # pyright: ignore[reportGeneralTypeIssues]
)
