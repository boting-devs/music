from __future__ import annotations

from os import environ

import uvloop

from .bot import Vibr
from .log import setup_logging

bot = Vibr()
setup_logging()
uvloop.install()
bot.run(environ["TOKEN"])
