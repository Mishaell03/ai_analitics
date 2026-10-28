-- Provider state belongs to the authenticated user's lesson conversation, not the browser.
ALTER TABLE ai_conversations ADD COLUMN provider_state JSONB NOT NULL DEFAULT '{}'::jsonb;
CREATE INDEX ix_ai_questions_created ON ai_questions (created_at);
