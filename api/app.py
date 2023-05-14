from contextlib import asynccontextmanager
from os import getenv

from botbase import database
from fastapi import FastAPI

from .routes import spotify

DEBUG = bool(getenv("DEV"))
DEV = bool(getenv("DEV"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()
    await spotify.init()

    yield

    await spotify.deinit()


app = FastAPI(debug=DEBUG, lifespan=lifespan)
app.include_router(spotify.router)
