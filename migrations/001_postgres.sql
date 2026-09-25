CREATE SCHEMA IF NOT EXISTS {schema};
CREATE TABLE IF NOT EXISTS {schema}.game_saves (
    sid text PRIMARY KEY,
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    revision bigint NOT NULL DEFAULT 1,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE IF NOT EXISTS {schema}.rate_limits (
    bucket text NOT NULL,
    identity text NOT NULL,
    expires_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS rate_limits_identity ON {schema}.rate_limits (bucket, identity);
CREATE INDEX IF NOT EXISTS rate_limits_expiry ON {schema}.rate_limits (expires_at);
CREATE TABLE IF NOT EXISTS {schema}.feedback (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payload jsonb NOT NULL
);
