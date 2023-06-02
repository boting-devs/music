from __future__ import annotations

from asyncio import sleep
from logging import getLogger

from botbase import CogBase
from nextcord import Permissions, slash_command
from nextcord.ext.application_checks import is_owner

from vibr.bot import Vibr
from vibr.constants import GUILD_IDS
from vibr.inter import Inter

log = getLogger(__name__)


class Management(CogBase[Vibr]):
    @slash_command(
        name="close-node",
        guild_ids=GUILD_IDS,
        default_member_permissions=Permissions(8),
    )
    @is_owner()
    async def close_node(self, inter: Inter, node: str) -> None:
        await inter.response.defer()
        actual_node = self.bot.pool.label_to_node[node]
        await self.bot.pool.remove_node(actual_node)

        await inter.send(f"Closed node {node}")

        for tries in range(10):
            try:
                await self.bot.pool.add_node(actual_node)
            except:  # noqa: E722
                log.warning(
                    "Failed to connect to node %s, retrying in %ds",
                    node,
                    2**tries,
                    exc_info=True,
                )
                await sleep(2**tries)
            else:
                break

        if actual_node.available:
            await inter.send("Successfully connected to node")
        else:
            await inter.send("Failed to connect to node")

    @close_node.on_autocomplete("node")
    async def close_node_autocomplete(self, inter: Inter, _node: str) -> None:
        await inter.response.send_autocomplete(list(self.bot.pool.label_to_node.keys()))


def setup(bot: Vibr) -> None:
    bot.add_cog(Management(bot))
