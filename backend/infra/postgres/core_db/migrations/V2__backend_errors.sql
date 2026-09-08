CREATE TABLE IF NOT EXISTS backend_errors (
    code VARCHAR(32) PRIMARY KEY,
    http_status INT NOT NULL
);
