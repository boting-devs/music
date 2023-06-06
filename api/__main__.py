import uvicorn
import uvloop

uvloop.install()
uvicorn.run(
    "api.app:app",
    host="0.0.0.0",  # noqa: S104
    port=8000,
)
