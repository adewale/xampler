DROP TABLE IF EXISTS workflow_timeline;

CREATE TABLE workflow_timeline (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instance_id TEXT NOT NULL,
  step TEXT NOT NULL,
  state TEXT NOT NULL,
  checkpoint TEXT,
  details TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_workflow_timeline_instance ON workflow_timeline(instance_id, id);
