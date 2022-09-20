from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from nextcord import Embed, Forbidden
from nextcord.ext.commands import Cog
from nextcord.ext.ipc import server
from nextcord.utils import get, utcnow

if TYPE_CHECKING:
    from ..__main__ import Vibr


class Ipc(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot

    @server.route()
    async def topgg(self, data) -> dict:
        user = data.user
        data_type = data.data_type

        if data_type == "upvote":
            user = int(user)
            votetime = utcnow() + timedelta(hours=24)
            await self.bot.db.execute(
                """INSERT INTO users (id, vote)
                VALUES ($1, $2)
                ON CONFLICT (id) DO UPDATE
                    SET vote=$2""",
                user,
                votetime,
            )
            self.bot.voted[user] = votetime
            user = await self.bot.fetch_user(user)
            embed = Embed(
                title="Thank You",
                description=f"Thank you for voting {user.name}, "
                "you can vote every 12 hours <3",
                color=self.bot.color,
            )

            lyrics_cmd = get(self.bot.get_all_application_commands(), name="lyrics")
            lyrics_mention = (
                lyrics_cmd.get_mention()  # pyright: ignore[reportGeneralTypeIssues]
                if lyrics_cmd
                else "`/lyrics`"
            )
            embed.add_field(
                name="Rewards", value=f"The ability to use {lyrics_mention}"
            )

            try:
                await user.send(embed=embed)
            except Forbidden:
                pass

            return {"response": True}
        else:
            return {"response": True}

    @Cog.listener()
    async def on_ipc_error(self, _, error: Exception):
        raise error


def setup(bot: Vibr):
    bot.add_cog(Ipc(bot))
