from __future__ import annotations

from typing import TYPE_CHECKING

from nextcord.ext.application_checks import check
from nextcord.utils import MISSING, utcnow

from .errors import NotConnected, VoteRequired

if TYPE_CHECKING:
    from nextcord import Interaction

    from ...__main__ import Vibr
    from .types import MyInter


__all__ = ("connected",)


def connected():
    async def extended_check(inter: MyInter) -> bool:
        if inter.guild.voice_client is None:
            raise NotConnected()

        return True

    return check(extended_check)  # type: ignore


def voted():
    async def inner(inter: Interaction[Vibr]) -> bool:
        assert inter.user is not None

        # Default to MISSING as we do not need to query every time it is missing.
        # But we do need to query if its not in the dict at all.
        voted = inter.client.voted.get(inter.user.id, MISSING)

        if voted is MISSING:
            voted = await inter.client.db.fetchval(
                "SELECT vote FROM users WHERE id=$1", inter.user.id
            )

            inter.client.voted[inter.user.id] = voted

        if voted is None or voted < utcnow():
            raise VoteRequired

        return True

    return check(inner)
