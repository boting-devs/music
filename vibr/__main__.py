from __future__ import annotations

import asyncio
import os
from datetime import datetime
from logging import DEBUG, getLogger
from traceback import format_exc
from typing import Optional

import nextcord
import uvloop
from botbase import BotBase
from dotenv import load_dotenv
from nextcord import Activity, ActivityType
from nextcord.ext.ipc import Server
from pomice import NodeConnectionFailure, NodePool
from spotipy import Spotify, SpotifyClientCredentials, SpotifyOauthError

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
load_dotenv()
log = getLogger(__name__)


class Vibr(BotBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pool = NodePool()
        self.views_added = False
        self.listeners: dict[int, set[int]] = {}
        self.spotify_users: dict[int, Optional[str]] = {}
        self.listener_tasks: dict[int, asyncio.Task[None]] = {}
        self.activity_tasks: dict[int, asyncio.Task[None]] = {}
        self.whitelisted_guilds: dict[int, datetime] = {}
        self.notified_users: set[int] = set()
        """A set of all users who have been notified, this is a cache.

        If a user needs to be checked on if they have been notified,
        if they are not in this set then they will be found in the db and either:

        - Added to this set as it is True.
        - Notified, then added to this set.
        """

        self.voted: dict[int, datetime | None] = {}
        """A dict of users who have voted, along with the time this expires.

        This is a cache of the `user` table's `id` and `vote` columns.
        """

        self.ipc = Server(
            self,
            host=os.environ["IPC_BIND"],
            port=int(os.environ["IPC_PORT"]),
            secret_key="pain.",
            do_multicast=False,
        )
        """The IPC server accessed by server/server.py for the top.gg webhook."""

        self.spotify: Spotify
        try:
            self.spotipy = Spotify(
                client_credentials_manager=SpotifyClientCredentials()
            )
        except SpotifyOauthError:
            log.warning("Spotify credentials are invalid")
            self.spotipy = None

        self.vote_webhook: nextcord.Webhook | None = None
        """The webhook in #vote-for-us for top.gg."""

        # env var BETA exists, set our logging to DEBUG (all loggings in `vibr/`)
        if os.getenv("BETA"):
            getLogger("vibr").setLevel(DEBUG)

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)

        for row in await self.db.fetch(
            "SELECT id, whitelisted FROM guilds WHERE whitelisted IS NOT NULL"
        ):
            self.whitelisted_guilds[row.get("id")] = row.get("whitelisted")
            log.debug(
                "Added whitelisted guild %s to cache, until %s",
                row.get("id"),
                row.get("whitelisted"),
            )

    async def on_ready(self):
        await asyncio.sleep(10)

        for tries in range(5):
            # Try 5 times to connect to the lavalink server.
            try:
                await self.pool.create_node(
                    bot=self,
                    host=os.environ["LAVALINK_HOST"],
                    port=os.getenv("LAVALINK_PORT", "6969"),
                    password="haha",
                    identifier="MAIN",
                    spotify_client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                    spotify_client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                )
            except NodeConnectionFailure:
                time = 2.5 * tries + 1
                log.warning("Failed to connect to lavalink, retrying in %ss", time)
                await asyncio.sleep(time)
            else:
                log.info("Successfully connected to %s", os.getenv("LAVALINK_HOST"))
                break

    async def on_error(self, event_method: str, *args, **kwargs):
        if self.logchannel is not None:
            painchannel = await self.getch_channel(self.logchannel)

            tb = format_exc()

            log.error(
                "Ignoring exception in event %s",
                event_method,
                exc_info=True,
            )

            try:
                await painchannel.send_embed(desc=f"```py\n{tb}```")
            except Exception:
                log.warning("Failed to send to logchannel %d", self.logchannel)


intents = nextcord.Intents.none()
intents.guilds = True
intents.messages = True  # This is to temporarily keep mentioned messages.
intents.voice_states = True
bot = Vibr(
    intents=intents,
    activity=Activity(type=ActivityType.listening, name="your beats :)"),
)


if __name__ == "__main__":
    # This is being ran with `python -m vibr`, and not an import, start ipc and the bot.
    bot.ipc.start()
    bot.run(os.getenv("TOKEN"))
