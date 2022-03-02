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

# REMOVE ON WINDOWS
import uvloop  # type: ignore

# REMOVE ON WINDOWS
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# REMOVE ON WINDOWS
load_dotenv()


class MyBot(BotBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pool = NodePool()
        self.views_added = False
        self.listeners: dict[int, set[int]] = {}
        self.spotify_users: dict[int, Optional[str]] = {}

        self.spotipy = Spotify(client_credentials_manager=SpotifyClientCredentials())

    async def on_ready(self):
        await self.pool.create_node(
            bot=self,
            host="127.0.0.1",
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
    case_insensitive=True,
    strip_after_prefix=True,
)


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
