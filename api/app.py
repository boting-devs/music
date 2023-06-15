from contextlib import asynccontextmanager
from os import getenv

from fastapi import FastAPI

DEBUG = bool(getenv("DEV"))
TOPGG_ENABLED = bool(getenv("TOPGG_ENABLED"))


@asynccontextmanager
async def lifetime(_: FastAPI):
    if TOPGG_ENABLED:
        from .routes.topgg import init

        await init()

    yield

    if TOPGG_ENABLED:
        from .routes.topgg import deinit

        await deinit()


app = FastAPI(debug=DEBUG, lifespan=lifetime)
if TOPGG_ENABLED:
    from .routes import topgg

    app.include_router(topgg.ROUTER)
