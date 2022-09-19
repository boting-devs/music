from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Optional

import nextcord
import nextcord.http
import uvloop
from botbase import BotBase
from dotenv import load_dotenv
from nextcord import Activity, ActivityType
from pomice import NodeConnectionFailure, NodePool
from spotipy import Spotify, SpotifyClientCredentials, SpotifyOauthError
from .cogs.extras.types import MyInter
from .cogs.extras.errors import ChannelDisabled

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
load_dotenv()


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

        self.spotify: Spotify
        try:
            self.spotipy = Spotify(
                client_credentials_manager=SpotifyClientCredentials()
            )
        except SpotifyOauthError:
            self.spotipy = None

    async def startup(self, *args, **kwargs):
        await super().startup(*args, **kwargs)

        for row in await self.db.fetch(
            "SELECT id, whitelisted FROM guilds WHERE whitelisted IS NOT NULL"
        ):
            self.whitelisted_guilds[row.get("id")] = row.get("whitelisted")

    async def on_ready(self):
        await asyncio.sleep(10)

        for tries in range(5):
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
                await asyncio.sleep(2.5 * tries)
            else:
                return


intents = nextcord.Intents.none()
intents.guilds = True
intents.messages = True  # This is to temporarily keep mentioned messages.
intents.voice_states = True
bot = Vibr(
    intents=intents,
    activity=Activity(type=ActivityType.listening, name="your beats :)"),
)


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
