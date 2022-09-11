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
    notified BOOLEAN NOT NULL DEFAULT FALSE
);