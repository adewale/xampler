CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY, quote TEXT NOT NULL, author TEXT NOT NULL);
DELETE FROM quotes;
INSERT INTO quotes (quote, author) VALUES ('Readability counts.', 'PEP 20');
