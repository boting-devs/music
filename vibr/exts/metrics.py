from __future__ import annotations

from botbase import CogBase
from prometheus_async.aio.web import MetricsHTTPServer, start_http_server

from vibr.bot import Vibr


class Prometheus(CogBase[Vibr]):
    def __init__(self, bot: Vibr) -> None:
        super().__init__(bot)
        self.metrics: MetricsHTTPServer | None = None

    @CogBase.listener()
    async def on_ready(self) -> None:
        if not self.metrics:
            self.metrics = await start_http_server(port=9000)

    async def cog_unload(self) -> None:
        if self.metrics:
            await self.metrics.close()


def setup(bot: Vibr) -> None:
    bot.add_cog(Prometheus(bot))
