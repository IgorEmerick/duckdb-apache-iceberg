-- Initial migration: create the bookkeeping table that records which
-- migrations have been applied. Idempotent so it is safe to re-run.
CREATE TABLE IF NOT EXISTS migrations (
  name VARCHAR,
  applied_at TIMESTAMP
);
