from __future__ import annotations

from datetime import UTC, datetime
from os import environ
from secrets import compare_digest
from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict

from fastapi import HTTPException, Request, status
from fastapi.routing import APIRouter

from vibr.db import User

if TYPE_CHECKING:

    class WebhookRequest(TypedDict):
        bot: str
        user: str
        type: Literal["upvote", "test"]
        isWeekend: bool
        query: NotRequired[str]


ROUTER = APIRouter(prefix="/topgg")
TOPGG_SECRET = environ["TOPGG_SECRET"]


@ROUTER.post("/webhook")
async def webhook(request: Request):
    if not (
        "Authorization" in request.headers
        and compare_digest(request.headers["Authorization"], TOPGG_SECRET)
    ):
        raise HTTPException(status.HTTP_418_IM_A_TEAPOT, detail="L")

    data: WebhookRequest = await request.json()

    if data["type"] == "test":
        return "OK!"

    await User.insert(
        User({User.id: int(data["user"]), User.topgg_voted: datetime.now(tz=UTC)})
    ).on_conflict((User.id,), "DO UPDATE", (User.topgg_voted,))

    return "OK!"
