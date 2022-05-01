from __future__ import annotations

from typing import Optional
import asyncio
import os

import nextcord
from nextcord import Activity, ActivityType
from botbase import BotBase
from dotenv import load_dotenv
from pomice import NodePool
from spotipy import Spotify, SpotifyClientCredentials
import uvloop


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
load_dotenv()


class MyBot(BotBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pool = NodePool()
        self.views_added = False
        self.listeners: dict[int, set[int]] = {}
        self.spotify_users: dict[int, Optional[str]] = {}
        self.listener_tasks: dict[int, asyncio.Task[None]] = {}

        self.spotipy = Spotify(client_credentials_manager=SpotifyClientCredentials())

    async def on_ready(self):
        await self.pool.create_node(
            bot=self,
            host="lavalink_default",
            port="6969",
            password="haha",
            identifier="MAIN",
            spotify_client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            spotify_client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        )


intents = nextcord.Intents.none()
intents.guilds = True
intents.messages = True
intents.voice_states = True
bot = MyBot(
    intents=intents,
    activity=Activity(type=ActivityType.listening, name="your beats :)"),
)


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
