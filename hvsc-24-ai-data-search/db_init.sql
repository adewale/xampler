CREATE TABLE IF NOT EXISTS releases (
  version INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  update_url TEXT NOT NULL,
  complete_url TEXT NOT NULL,
  summary TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_releases_version ON releases(version);
DELETE FROM releases;
PRAGMA optimize;
