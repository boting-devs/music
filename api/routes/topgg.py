from __future__ import annotations

from asyncio import Task, create_task
from datetime import UTC, datetime
from os import environ
from secrets import compare_digest
from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict, cast

import nextcord
from fastapi import HTTPException, Request, status
from fastapi.routing import APIRouter
from nextcord import Intents, TextChannel, Webhook
from nextcord.utils import get

if TYPE_CHECKING:

    class WebhookRequest(TypedDict):
        bot: str
        user: str
        type: Literal["upvote", "test"]
        isWeekend: bool
        query: NotRequired[str]


WEBHOOK_NAME = "Vibr Vote"
ROUTER = APIRouter(prefix="/topgg")
TOPGG_SECRET = environ["TOPGG_SECRET"]
DISCORD_TOKEN = environ["DISCORD_TOKEN"]
VOTE_CHANNEL = int(environ["VOTE_CHANNEL"])


class Client(nextcord.Client):
    def __init__(self) -> None:
        super().__init__(intents=Intents(guilds=True))
        self.vote_webhook: Webhook | None = None


client = Client()
task: Task | None = None


async def init() -> None:
    global task  # noqa: PLW0603
    task = create_task(client.start(DISCORD_TOKEN))


async def deinit() -> None:
    if task:
        task.cancel()
    await client.close()


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

    user = int(data["user"])
    # await User.insert(
    #     User({User.id: user, User.topgg_voted: datetime.now(tz=UTC)})
    # ).on_conflict((User.id,), "DO UPDATE", (User.topgg_voted,))

    if client.vote_webhook:
        webhook = client.vote_webhook
    else:
        channel = cast(TextChannel, await client.fetch_channel(VOTE_CHANNEL))
        webhooks = await channel.webhooks()
        assert client.user is not None
        webhook = get(webhooks, name=WEBHOOK_NAME, user__id=client.user.id)
        if not webhook:
            webhook = await channel.create_webhook(
                name=WEBHOOK_NAME, avatar=client.user.avatar
            )

        client.vote_webhook = webhook

    user = await client.fetch_user(user)
    display = str(user) if user.discriminator != "0" else user.display_name
    await webhook.send(
        content=f"`{display}` has voted",
        username=user.display_name,
        avatar_url=user.display_avatar.url,
    )

    return "OK!"
