-- Add new columns to the spans table for storing input/output content
ALTER TABLE policy_aide.spans
ADD COLUMN IF NOT EXISTS input_text TEXT,
ADD COLUMN IF NOT EXISTS output_text TEXT,
ADD COLUMN IF NOT EXISTS model VARCHAR(100),
ADD COLUMN IF NOT EXISTS tokens_used JSONB;

-- Create an index on agent_name for faster lookups
CREATE INDEX IF NOT EXISTS idx_spans_agent_name ON policy_aide.spans(agent_name);

-- Sample query to test retrieving traces with content
-- SELECT 
--     t.trace_id,
--     t.policy_query,
--     t.policy_type,
--     s.span_id,
--     s.agent_name,
--     s.span_type,
--     s.input_text,
--     s.output_text,
--     s.model,
--     s.tokens_used
-- FROM 
--     policy_aide.traces t
-- JOIN 
--     policy_aide.spans s ON t.trace_id = s.trace_id
-- WHERE 
--     t.policy_type = 'analysis'
-- ORDER BY 
--     t.created_at DESC, s.started_at ASC
-- LIMIT 100; 