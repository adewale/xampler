CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY, quote TEXT NOT NULL, author TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_quotes_author ON quotes(author);
DELETE FROM quotes;
INSERT INTO quotes (quote, author) VALUES ('Readability counts.', 'PEP 20');
PRAGMA optimize;
