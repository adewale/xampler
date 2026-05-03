CREATE TABLE IF NOT EXISTS gutenberg_chunks (
  chunk_no INTEGER PRIMARY KEY,
  text TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS gutenberg_fts USING fts5(
  chunk_no UNINDEXED,
  text
);

CREATE TABLE IF NOT EXISTS gutenberg_pipeline_lines (
  line_no INTEGER PRIMARY KEY,
  text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stream_checkpoints (
  name TEXT PRIMARY KEY,
  offset INTEGER NOT NULL,
  records INTEGER NOT NULL,
  state TEXT NOT NULL
);
