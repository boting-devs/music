from __future__ import annotations

from os import environ

import uvloop

from .bot import Vibr

bot = Vibr()

if __name__ == "__main__":
    uvloop.install()
    bot.run(environ["TOKEN"])
