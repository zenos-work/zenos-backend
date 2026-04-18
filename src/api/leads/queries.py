"""Phase 5 Step 25 — Lead-generation SQL queries."""

# ── Lead Capture Forms ───────────────────────────────────────
LIST_FORMS = (
    "SELECT * FROM lead_capture_forms WHERE org_id = ? ORDER BY created_at DESC"
)
GET_FORM = "SELECT * FROM lead_capture_forms WHERE id = ?"
INSERT_FORM = """INSERT INTO lead_capture_forms
  (id, org_id, owner_id, name, slug, description, placement, fields_schema,
   submit_button_text, success_message, redirect_url, tags_on_submit,
   workflow_id, is_active)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_FORM = """UPDATE lead_capture_forms
  SET name = ?, description = ?, placement = ?, fields_schema = ?,
      submit_button_text = ?, success_message = ?, redirect_url = ?,
      tags_on_submit = ?, workflow_id = ?, is_active = ?,
      updated_at = datetime('now')
  WHERE id = ?"""
DELETE_FORM = "DELETE FROM lead_capture_forms WHERE id = ?"
INC_FORM_SUBMISSIONS = """UPDATE lead_capture_forms
  SET submission_count = submission_count + 1 WHERE id = ?"""

# ── Leads ────────────────────────────────────────────────────
LIST_LEADS = """SELECT * FROM leads WHERE org_id = ?
  ORDER BY created_at DESC LIMIT ? OFFSET ?"""
LIST_LEADS_BY_STATUS = """SELECT * FROM leads WHERE org_id = ? AND status = ?
  ORDER BY created_at DESC LIMIT ? OFFSET ?"""
GET_LEAD = "SELECT * FROM leads WHERE id = ?"
GET_LEAD_BY_EMAIL = "SELECT * FROM leads WHERE org_id = ? AND email = ?"
INSERT_LEAD = """INSERT INTO leads
  (id, org_id, email, first_name, last_name, company, job_title, phone,
   source, source_detail, utm_source, utm_medium, utm_campaign, utm_term, utm_content,
   referrer_url, landing_page, capture_form_id, custom_fields, score, status,
   consent_email, consent_tracking, consent_at, ip_address, user_agent)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'new', ?, ?, ?, ?, ?)"""
UPDATE_LEAD = """UPDATE leads
  SET first_name = ?, last_name = ?, company = ?, job_title = ?,
      status = ?, custom_fields = ?, updated_at = datetime('now')
  WHERE id = ?"""
UPDATE_LEAD_SCORE = "UPDATE leads SET score = score + ? WHERE id = ?"
DELETE_LEAD = "DELETE FROM leads WHERE id = ?"

# ── Lead Tags ────────────────────────────────────────────────
LIST_LEAD_TAGS = "SELECT tag FROM lead_tags WHERE org_id = ? AND lead_id = ?"
ADD_LEAD_TAG = "INSERT OR IGNORE INTO lead_tags (org_id, lead_id, tag) VALUES (?, ?, ?)"
REMOVE_LEAD_TAG = "DELETE FROM lead_tags WHERE org_id = ? AND lead_id = ? AND tag = ?"

# ── Lead Events ──────────────────────────────────────────────
LIST_LEAD_EVENTS = """SELECT * FROM lead_events WHERE lead_id = ?
  ORDER BY created_at DESC LIMIT ? OFFSET ?"""
INSERT_LEAD_EVENT = """INSERT INTO lead_events
  (id, lead_id, org_id, event_type, metadata, actor_id)
  VALUES (?, ?, ?, ?, ?, ?)"""

# ── Lead Score Rules ─────────────────────────────────────────
LIST_SCORE_RULES = "SELECT * FROM lead_score_rules WHERE org_id = ? ORDER BY name"
GET_SCORE_RULE = "SELECT * FROM lead_score_rules WHERE id = ?"
INSERT_SCORE_RULE = """INSERT INTO lead_score_rules
  (id, org_id, name, trigger_event, condition, score_delta, is_active)
  VALUES (?, ?, ?, ?, ?, ?, ?)"""
UPDATE_SCORE_RULE = """UPDATE lead_score_rules
  SET name = ?, trigger_event = ?, condition = ?, score_delta = ?, is_active = ?
  WHERE id = ?"""
DELETE_SCORE_RULE = "DELETE FROM lead_score_rules WHERE id = ?"

# ── Lead Pipelines ───────────────────────────────────────────
LIST_PIPELINES = "SELECT * FROM lead_pipelines WHERE org_id = ? ORDER BY sort_order"
GET_PIPELINE = "SELECT * FROM lead_pipelines WHERE id = ?"
INSERT_PIPELINE = """INSERT INTO lead_pipelines
  (id, org_id, name, description, sort_order) VALUES (?, ?, ?, ?, ?)"""
UPDATE_PIPELINE = """UPDATE lead_pipelines
  SET name = ?, description = ?, sort_order = ? WHERE id = ?"""
DELETE_PIPELINE = "DELETE FROM lead_pipelines WHERE id = ?"

# ── Pipeline Stages ──────────────────────────────────────────
LIST_STAGES = "SELECT * FROM pipeline_stages WHERE pipeline_id = ? ORDER BY sort_order"
GET_STAGE = "SELECT * FROM pipeline_stages WHERE id = ?"
INSERT_STAGE = """INSERT INTO pipeline_stages
  (id, pipeline_id, name, sort_order, stage_type, color) VALUES (?, ?, ?, ?, ?, ?)"""
UPDATE_STAGE = """UPDATE pipeline_stages
  SET name = ?, sort_order = ?, stage_type = ?, color = ? WHERE id = ?"""
DELETE_STAGE = "DELETE FROM pipeline_stages WHERE id = ?"

# ── Lead Pipeline Entries ────────────────────────────────────
LIST_PIPELINE_ENTRIES = """SELECT * FROM lead_pipeline_entries
  WHERE pipeline_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"""
GET_PIPELINE_ENTRY = "SELECT * FROM lead_pipeline_entries WHERE id = ?"
INSERT_PIPELINE_ENTRY = """INSERT INTO lead_pipeline_entries
  (id, lead_id, pipeline_id, stage_id, assigned_to, deal_value, notes)
  VALUES (?, ?, ?, ?, ?, ?, ?)"""
UPDATE_PIPELINE_ENTRY = """UPDATE lead_pipeline_entries
  SET stage_id = ?, assigned_to = ?, deal_value = ?, notes = ?,
      entered_stage_at = datetime('now'), updated_at = datetime('now')
  WHERE id = ?"""
DELETE_PIPELINE_ENTRY = "DELETE FROM lead_pipeline_entries WHERE id = ?"

# ── Email Sequences ──────────────────────────────────────────
LIST_SEQUENCES = (
    "SELECT * FROM email_sequences WHERE org_id = ? ORDER BY created_at DESC"
)
GET_SEQUENCE = "SELECT * FROM email_sequences WHERE id = ?"
INSERT_SEQUENCE = """INSERT INTO email_sequences
  (id, org_id, name, description, trigger_type, status, created_by)
  VALUES (?, ?, ?, ?, ?, 'draft', ?)"""
UPDATE_SEQUENCE = """UPDATE email_sequences
  SET name = ?, description = ?, trigger_type = ?, status = ?,
      updated_at = datetime('now') WHERE id = ?"""
DELETE_SEQUENCE = "DELETE FROM email_sequences WHERE id = ?"

# ── Email Sequence Steps ─────────────────────────────────────
LIST_STEPS = (
    "SELECT * FROM email_sequence_steps WHERE sequence_id = ? ORDER BY step_number"
)
GET_STEP = "SELECT * FROM email_sequence_steps WHERE id = ?"
INSERT_STEP = """INSERT INTO email_sequence_steps
  (id, sequence_id, step_number, delay_days, subject, body_html, body_text)
  VALUES (?, ?, ?, ?, ?, ?, ?)"""
UPDATE_STEP = """UPDATE email_sequence_steps
  SET delay_days = ?, subject = ?, body_html = ?, body_text = ? WHERE id = ?"""
DELETE_STEP = "DELETE FROM email_sequence_steps WHERE id = ?"

# ── Lead Sequence Enrollments ────────────────────────────────
LIST_ENROLLMENTS = """SELECT * FROM lead_sequence_enrollments
  WHERE sequence_id = ? ORDER BY enrolled_at DESC LIMIT ? OFFSET ?"""
GET_ENROLLMENT = "SELECT * FROM lead_sequence_enrollments WHERE id = ?"
INSERT_ENROLLMENT = """INSERT INTO lead_sequence_enrollments
  (id, lead_id, sequence_id, current_step, status)
  VALUES (?, ?, ?, 0, 'active')"""
UPDATE_ENROLLMENT = """UPDATE lead_sequence_enrollments
  SET current_step = ?, status = ?, last_step_at = datetime('now') WHERE id = ?"""
