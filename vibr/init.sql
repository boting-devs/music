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
    volume SMALLINT,
    --- Stored as bytes as that is what orjson loves, saves conversion.
    position BIGINT,
    tracks BYTEA[]
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
    total_songs INT NOT NULL,
    listeners BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL DEFAULT 'Liked Songs',
    owner BIGINT REFERENCES users(id) ON DELETE CASCADE,
    description VARCHAR NOT NULL DEFAULT '',
    UNIQUE (name, owner)
);

CREATE TABLE IF NOT EXISTS song_data (
    id VARCHAR PRIMARY KEY,
    lavalink_id VARCHAR NOT NULL,
    spotify BOOLEAN NOT NULL,
    name VARCHAR NOT NULL,
    artist VARCHAR NOT NULL,
    length INT NOT NULL,
    thumbnail VARCHAR NOT NULL,
    uri VARCHAR NOT NULL,
    likes INT NOT NULL DEFAULT 0,
);

-- Junction table with a composite primary key - many to many relation.
CREATE TABLE IF NOT EXISTS song_to_playlist (
    song VARCHAR NOT NULL REFERENCES song_data(id) ON DELETE CASCADE,
    playlist INT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    added TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(song, playlist)
);
