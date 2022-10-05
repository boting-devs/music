from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from nextcord import Embed, HTTPException, TextChannel
from nextcord.ext.commands import Cog
from nextcord.ext.ipc import server
from nextcord.utils import get, utcnow
from vibr.config import vote_channel

if TYPE_CHECKING:
    from ..__main__ import Vibr


class Ipc(Cog):
    def __init__(self, bot: Vibr):
        self.bot = bot

    @server.route()
    async def topgg(self, data) -> dict:
        user = data.user
        data_type = data.data_type

        # top.gg is telling us about a vote
        if data_type == "upvote":
            user = int(user)
            # The time when the vote expires
            votetime = utcnow() + timedelta(hours=24)
            await self.bot.db.execute(
                """INSERT INTO users (id, vote)
                VALUES ($1, $2)
                ON CONFLICT (id) DO UPDATE
                    SET vote=$2""",
                user,
                votetime,
            )
            # Cache the time their vote status persists, so we do not need to fetch.
            self.bot.voted[user] = votetime
            user = await self.bot.fetch_user(user)
            embed = Embed(
                title="Thank You",
                description=f"Thank you for voting {user.name}, "
                "you can vote every 12 hours <3",
                color=self.bot.color,
            )

            # Cache and create if needed
            if self.bot.vote_webhook is None:
                channel = self.bot.get_channel(vote_channel)
                if channel is not None and isinstance(channel, TextChannel):
                    webhooks = await channel.webhooks()
                    webhook = get(webhooks, name="Vibr Vote")

                    if webhook is None:
                        assert self.bot.user is not None
                        webhook = await channel.create_webhook(
                            name="Vibr Vote", avatar=self.bot.user.avatar
                        )

                    self.bot.vote_webhook = webhook

            # Hopefully we found the channel
            if self.bot.vote_webhook is not None:
                await self.bot.vote_webhook.send(
                    f"`{user}` has voted",
                    avatar_url=user.display_avatar.url,
                    username=user.display_name,
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
            except HTTPException:
                # Ignore failed to send errors.
                pass

            return {"response": True}
        else:
            # Probably a test.
            return {"response": True}

    @Cog.listener()
    async def on_ipc_error(self, _, error: Exception):
        # Propegate to our own on_error handler.
        raise error


def setup(bot: Vibr):
    bot.add_cog(Ipc(bot))
