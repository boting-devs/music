from __future__ import annotations

from asyncio import sleep
from os import getenv

from botbase import CogBase
from nextcord.ext.tasks import loop

from vibr.bot import Vibr

TOKEN = getenv("TOPGG_TOKEN")


class Topgg(CogBase[Vibr]):
    @CogBase.listener()
    async def on_ready(self) -> None:
        if not self.post_stats.is_running() and TOKEN:
            self.post_stats.start()

    def cog_unload(self) -> None:
        self.post_stats.stop()

    async def aquire_connection(self, shard_id: int, tries: int = 5) -> None:
        ratelimit = await self.bot.redis.get("topgg")
        if not ratelimit:
            await self.bot.redis.set("topgg", 60, ex=60)
            return

        if ratelimit == 0:
            expiry = await self.bot.redis.ttl("topgg")
            await sleep(expiry + shard_id)
            await self.aquire_connection(shard_id, tries=tries - 1)
            return

    @loop(minutes=30)
    async def post_stats(self) -> None:
        headers = {"Authorization": TOKEN}

        for shard in self.bot.shard_ids or []:
            await self.aquire_connection(shard)
            data = {
                "server_count": sum(g.shard_id == shard for g in self.bot.guilds),
                "shard_id": shard,
                "shard_count": self.bot.shard_count,
            }
            assert self.bot.user is not None
            await self.bot.session.post(
                f"https://top.gg/api/bots/{self.bot.user.id}/stats",
                headers=headers,
                data=data,
            )
            await sleep(1)

    @post_stats.before_loop
    async def before_loop(self) -> None:
        await self.bot.wait_until_ready()
        # Just to be safe.
        await sleep(60 * 30)


def setup(bot: Vibr) -> None:
    bot.add_cog(Topgg(bot))
