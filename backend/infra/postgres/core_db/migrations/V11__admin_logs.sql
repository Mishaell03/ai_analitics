ALTER TABLE backend_error_logs ADD COLUMN error_code VARCHAR(255);

CREATE INDEX ix_backend_error_logs_created ON backend_error_logs (created_at DESC, id DESC);
CREATE INDEX ix_backend_error_logs_code_created ON backend_error_logs (error_code, created_at DESC);
CREATE INDEX ix_users_event_logs_created ON users_event_logs (created_at DESC, id DESC);
CREATE INDEX ix_users_event_logs_event_created ON users_event_logs (event, created_at DESC);
CREATE INDEX ix_users_event_logs_user_created ON users_event_logs (user_id, created_at DESC);
CREATE INDEX ix_users_event_logs_session_created ON users_event_logs (session_id, created_at DESC);
CREATE INDEX ix_backend_error_logs_session_created ON backend_error_logs (session_id, created_at DESC);
CREATE INDEX ix_ai_questions_created_question ON ai_questions (created_at DESC, question_id DESC);
