from __future__ import annotations

from os import environ

import uvloop

from .bot import Vibr
from .log import setup_logging

bot = Vibr()
__import__("logging").getLogger("nextcord").setLevel("DEBUG")
setup_logging()
uvloop.install()
bot.run(environ["TOKEN"])
