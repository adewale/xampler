CREATE TABLE IF NOT EXISTS gutenberg_chunks (
  chunk_no INTEGER PRIMARY KEY,
  text TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS gutenberg_fts USING fts5(
  chunk_no UNINDEXED,
  text
);
