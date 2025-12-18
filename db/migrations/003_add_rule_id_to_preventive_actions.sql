-- Migration: 003_add_rule_id_to_preventive_actions
-- Purpose: Forward migration for existing DBs created before rule_id was added.

BEGIN;

ALTER TABLE preventive_actions
  ADD COLUMN IF NOT EXISTS rule_id TEXT;

-- Backfill to keep NOT NULL semantics for new codepaths.
UPDATE preventive_actions
SET rule_id = ''
WHERE rule_id IS NULL;

ALTER TABLE preventive_actions
  ALTER COLUMN rule_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_actions_rule_id ON preventive_actions(rule_id);

COMMIT;
