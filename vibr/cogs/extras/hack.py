# help
from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from nextcord import Interaction, Member, User
from nextcord.types.interactions import ApplicationCommandInteractionData
from pomice import Node, Track

from .types import MyInter

if TYPE_CHECKING:
    from nextcord.types.interactions import Interaction as InteractionPayload
    from nextcord.types.member import MemberWithUser as MemberWithUserPayload
    from nextcord.types.user import User as UserPayload

    from ...__main__ import Vibr


def serialise_user(user: User) -> UserPayload:
    return {
        "id": user.id,
        "username": user.name,
        "discriminator": user.discriminator,
        "avatar": user.avatar.key if user.avatar is not None else None,
        "bot": user.bot,
        "public_flags": user.public_flags.value,
        "system": user.system,
    }


def serialise_member(member: Member) -> MemberWithUserPayload:
    data: MemberWithUserPayload = {
        "roles": [r.id for r in member.roles],
        "joined_at": member.joined_at.isoformat()
        if member.joined_at is not None
        else None,  # type: ignore
        # No idea why these are required or even exist.
        "deaf": str(False),
        "mute": str(False),
        "pending": member.pending,
        "user": serialise_user(member._user),
        "permissions": str(member.guild_permissions.value),
    }

    if member.avatar is not None:
        data["avatar"] = member.avatar.key

    if member.nick is not None:
        data["nick"] = member.nick

    if member.premium_since is not None:
        data["premium_since"] = member.premium_since.isoformat()

    if member.communication_disabled_until is not None:
        data[
            "communication_disabled_until"  # type: ignore
        ] = member.communication_disabled_until.isoformat()

    return data


def serialise_inter(inter: MyInter) -> InteractionPayload:
    data: InteractionPayload = {
        "id": inter.id,
        "application_id": inter.application_id,
        "type": inter.type.value,
        "token": inter.token,
        "version": inter.version,
        "app_permissions": str(inter.app_permissions.value),
    }

    if inter.channel_id is not None:
        data["channel_id"] = inter.channel_id

    if inter.data is not None:
        data["data"] = {
            "id": inter.data["id"],  # type: ignore
            "name": inter.data["name"],  # type: ignore
            "type": inter.data["type"],  # type: ignore
        }

    if inter.guild_id is not None:
        data["guild_id"] = inter.guild_id

    if inter.guild_locale is not None:
        data["guild_locale"] = inter.guild_locale

    if inter.locale is not None:
        data["locale"] = inter.locale

    if isinstance(inter.user, Member):
        data["member"] = serialise_member(inter.user)  # type: ignore
    elif isinstance(inter.user, User):
        data["user"] = serialise_user(inter.user)

    return data


class SerialisedTrack(TypedDict):
    id: str
    spotify: bool
    info: dict
    inter: InteractionPayload


def serialise_track(track: Track) -> SerialisedTrack:
    """Serialise a track to a json parsable dict."""

    data: SerialisedTrack = {
        "id": track.track_id,
        "spotify": track.spotify,
        "info": track.info,
        "inter": serialise_inter(track.ctx),  # type: ignore
    }

    return data


async def parse_track(*, node: Node, data: SerialisedTrack, bot: Vibr) -> Track:
    """Parse a track from a dict."""

    return Track(
        track_id=data["id"],
        info=data["info"],
        spotify=data["spotify"],
        ctx=MyInter(Interaction(data=data["inter"], state=bot._connection), bot),  # type: ignore
    )
