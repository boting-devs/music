ALTER TABLE guilds ADD COLUMN IF NOT EXISTS whitelisted TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    notification TEXT NOT NULL,
    datetime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS songs (
    id VARCHAR NOT NULL PRIMARY KEY,
    spotify BOOLEAN NOT NULL,
    member BIGINT NOT NULL,
    amount INTEGER NOT NULL DEFAULT 1,
    UNIQUE(id, spotify, member)
);
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    spotify VARCHAR,
    notified BOOLEAN NOT NULL DEFAULT FALSE,
    vote TIMESTAMPTZ,
    total_time INT
);
CREATE TABLE IF NOT EXISTS players (
    channel BIGINT PRIMARY KEY,
    volume SMALLINT
);
-- This uh, will need changing...at 32678 guilds/32678 MiB RAM, lmao, in my dreams

CREATE TABLE IF NOT EXISTS hourly_stats (
    time TIMESTAMPTZ PRIMARY KEY,
    guilds SMALLINT NOT NULL,
    commands INT NOT NULL,
    active_players SMALLINT NOT NULL,
    total_players SMALLINT NOT NULL,
    lavalink_load REAL NOT NULL,
    system_load REAL NOT NULL,
    memory_used SMALLINT NOT NULL,
    memory_allocated SMALLINT NOT NULL,
    memory_percentage SMALLINT NOT NULL,
    total_songs INT NOT NULL
)
