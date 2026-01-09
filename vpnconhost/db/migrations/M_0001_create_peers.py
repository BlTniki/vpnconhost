scripts = ["""
CREATE TABLE IF NOT EXISTS peers (
    peer_id TEXT PRIMARY KEY,
    peer_ip TEXT NOT NULL PRIMARY KEY,
    peer_public_key TEXT NOT NULL,
    peer_private_key TEXT NOT NULL,
    is_activated BOOLEAN NOT NULL DEFAULT 0
);
"""]
