from os import getenv

from fastapi import FastAPI

DEBUG = bool(getenv("DEV"))
TOPGG_ENABLED = bool(getenv("TOPGG_ENABLED"))


app = FastAPI(debug=DEBUG)
if TOPGG_ENABLED:
    from .routes import topgg
    app.include_router(topgg.ROUTER)
