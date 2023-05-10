from __future__ import annotations

from os import environ

import uvloop

from .bot import Vibr

bot = Vibr()

uvloop.install()
bot.run(environ["TOKEN"])
