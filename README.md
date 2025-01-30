# Music

The source code for the music bot Vibr, reaching 150K servers, 20M command uses, and 35M songs played.

This was ran with 4 separate processes connected together to individually handle tens of shards, for a max of 196 at its peak (Discord recommended shard value).

> [!NOTE]
> This repository is no longer maintained. The source code is provided as-is and will not be updated.
> I recommend if you would like to maintain your own bot, to use some of the tools below (~~especially mafic~~).

## Tools

- [Lavalink](https://github.com/lavalink-devs/lavalink) as the voice client and music server.
- [Mafic](https://github.com/ooliver1/mafic) as the lavalink API wrapper.
- [Nextcord](https://github.com/nextcord/nextcord) as the Discord API wrapper.
- [gateway-proxy](https://github.com/Gelbpunkt/gateway-proxy) ([Fork](https://github.com/ooliver1/gateway-proxy)) to handle all shards and split them between processes.
- [Piccolo](https://github.com/piccolo-orm/piccolo) as the ORM for the database.
- [AsyncSpotify](https://github.com/NiclasHaderer/AsyncSpotify) ([Fork](https://github.com/ooliver1/AsyncSpotify)) as the Spotify API wrapper.
