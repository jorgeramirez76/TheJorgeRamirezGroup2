PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT,
  last_name TEXT,
  phones TEXT NOT NULL DEFAULT '[]',
  emails TEXT NOT NULL DEFAULT '[]',
  address TEXT,
  town TEXT,
  county TEXT,
  source TEXT,
  source_detail TEXT,
  utm TEXT NOT NULL DEFAULT '{}',
  timezone TEXT NOT NULL DEFAULT 'America/New_York',
  imessage_handle TEXT,
  preferred_channel TEXT CHECK (preferred_channel IN ('imessage','email') OR preferred_channel IS NULL),
  consent_sms INTEGER NOT NULL DEFAULT 0,
  consent_email INTEGER NOT NULL DEFAULT 0,
  consent_source TEXT,
  consent_at TEXT,
  do_not_contact INTEGER NOT NULL DEFAULT 0,
  archived INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS contact_tags (contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE, tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE, PRIMARY KEY(contact_id, tag_id));
CREATE TABLE IF NOT EXISTS custom_fields (contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE, key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(contact_id, key));
CREATE TABLE IF NOT EXISTS pipelines (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS stages (id INTEGER PRIMARY KEY AUTOINCREMENT, pipeline_id INTEGER NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE, name TEXT NOT NULL, position INTEGER NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS stages_pipeline_position_idx ON stages(pipeline_id, position);
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
  pipeline_id INTEGER NOT NULL REFERENCES pipelines(id) ON DELETE RESTRICT,
  stage_id INTEGER NOT NULL REFERENCES stages(id) ON DELETE RESTRICT,
  intent TEXT NOT NULL CHECK (intent IN ('buy','sell','both')),
  score INTEGER NOT NULL DEFAULT 0,
  score_breakdown TEXT NOT NULL DEFAULT '{}',
  temperature TEXT NOT NULL DEFAULT 'COLD' CHECK (temperature IN ('HOT','WARM','COLD')),
  assigned_autonomy TEXT NOT NULL DEFAULT 'approval' CHECK (assigned_autonomy IN ('approval','guarded','full')),
  stage_entered_at TEXT,
  next_touch_at TEXT,
  last_inbound_at TEXT,
  last_outbound_at TEXT,
  video_sent_at TEXT,
  appointment_at TEXT,
  closed_reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
  channel TEXT NOT NULL CHECK (channel IN ('imessage','email','note','call_log','video')),
  direction TEXT NOT NULL CHECK (direction IN ('in','out')),
  body TEXT NOT NULL,
  subject TEXT,
  attachments TEXT NOT NULL DEFAULT '[]',
  external_id TEXT,
  thread_key TEXT,
  status TEXT NOT NULL CHECK (status IN ('queued','awaiting_approval','sent','delivered','read','failed','received')),
  generated_by TEXT CHECK (generated_by IN ('ai','human','workflow_template') OR generated_by IS NULL),
  model_used TEXT,
  tokens_in INTEGER,
  tokens_out INTEGER,
  error TEXT,
  sent_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS messages_channel_external_id_idx ON messages(channel, external_id);
CREATE TABLE IF NOT EXISTS conversation_summaries (contact_id INTEGER PRIMARY KEY REFERENCES contacts(id) ON DELETE CASCADE, summary TEXT NOT NULL, facts TEXT NOT NULL DEFAULT '{}', last_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS workflows (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, trigger TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS workflow_steps (id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE, position INTEGER NOT NULL, step TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS workflow_steps_workflow_position_idx ON workflow_steps(workflow_id, position);
CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE, lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE, current_step INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL DEFAULT 'active' CHECK (state IN ('active','paused','completed','exited')), wake_at TEXT, context TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS scheduled_actions (id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE, kind TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}', run_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','completed','failed','cancelled')), attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL, kind TEXT NOT NULL, payload TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE, script TEXT NOT NULL, higgsfield_job_id TEXT, status TEXT NOT NULL DEFAULT 'scripted' CHECK (status IN ('scripted','queued','rendering','ready','sent','failed')), video_url TEXT, thumb_url TEXT, watch_events TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS suppressions (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL CHECK (kind IN ('phone','email','contact')), value TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE UNIQUE INDEX IF NOT EXISTS suppressions_kind_value_idx ON suppressions(kind, value);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, actor TEXT NOT NULL, action TEXT NOT NULL, entity TEXT NOT NULL, entity_id TEXT, detail TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
