# Environments

## Running

### Local

```bash
docker-compose up --build
```

### Production

```bash
docker-compose up -d --build -f docker-compose.prod.yml
```

### Beta

```bash
docker-compose up -d --build -f docker-compose.beta.yml
```

## Differences

### Alpha

Does not use host network, all networking is contained inside docker. This means that the host needs to be exposed with `0.0.0.0` and accessed with `lavalink` as the compose link.

### Beta

Uses host network for ratelimit IPv6 block connections so only needs host `127.0.0.1`/`localhost`, but also port `6968` to reduce port conflict. Uses a docker postgres container but on port `5433` to not clash with the main bot.

### Production

Uses host network. Uses host postgres with unix socket for performance and so it is exposed for pgadmin safely.
