CREATE TABLE IF NOT EXISTS releases (
  version INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  update_url TEXT NOT NULL,
  complete_url TEXT NOT NULL,
  summary TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_releases_version ON releases(version);

CREATE TABLE IF NOT EXISTS tracks (
  id TEXT PRIMARY KEY,
  version INTEGER NOT NULL,
  path TEXT NOT NULL,
  filename TEXT NOT NULL,
  title TEXT,
  composer TEXT,
  search_text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tracks_composer ON tracks(composer);
CREATE INDEX IF NOT EXISTS idx_tracks_search_text ON tracks(search_text);

DELETE FROM releases;
DELETE FROM tracks;
PRAGMA optimize;
