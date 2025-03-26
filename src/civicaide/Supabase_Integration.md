# CivicAide Database Implementation Report

## Overview

This report documents the setup and configuration of a PostgreSQL database within Supabase for the CivicAide platform, with a particular focus on storing agent trace data from policy analysis workflows. The database is designed to support both the PolicyAide tool and potential future extensions of the CivicAide platform.

## Database Structure

The database is organized into multiple schemas to maintain clear separation between different components:

### `policy_aide` Schema
- **traces**: Stores high-level information about policy analysis traces
  - `trace_id VARCHAR(50) PRIMARY KEY`: Unique identifier for the trace
  - `policy_query TEXT`: The policy question being analyzed
  - `policy_type VARCHAR(50)`: Type of policy analysis (research, analysis, evolution, integrated)
  - `created_at TIMESTAMP WITH TIME ZONE`: When the trace was created
  - `openai_trace_id VARCHAR(50)`: Reference to OpenAI's trace ID if available
  - `agent_count INTEGER`: Number of agents involved in the trace
  - `total_duration_ms INTEGER`: Total duration of the trace in milliseconds
  - `metadata JSONB`: Additional flexible metadata

- **spans**: Stores detailed information about individual steps in a trace
  - `span_id VARCHAR(50) PRIMARY KEY`: Unique identifier for the span
  - `trace_id VARCHAR(50) REFERENCES policy_aide.traces(trace_id)`: Link to parent trace
  - `parent_span_id VARCHAR(50)`: Link to parent span (for hierarchical spans)
  - `span_type VARCHAR(100)`: Type of operation (research, analysis, etc.)
  - `agent_name VARCHAR(100)`: Name of the agent performing the operation
  - `started_at TIMESTAMP WITH TIME ZONE`: Start time of the span
  - `ended_at TIMESTAMP WITH TIME ZONE`: End time of the span
  - `duration_ms INTEGER`: Duration of the span in milliseconds
  - `span_data JSONB`: Complete span data including inputs, outputs, etc.

### `public` Schema
- **profiles**: Stores user profile information
  - `id UUID PRIMARY KEY REFERENCES auth.users(id)`: User ID
  - `full_name TEXT`: User's full name
  - `jurisdiction TEXT`: User's jurisdiction
  - `role TEXT`: User's role
  - `created_at TIMESTAMP WITH TIME ZONE`: When the profile was created
  - `updated_at TIMESTAMP WITH TIME ZONE`: When the profile was last updated

- **communities**: Stores information about communities/jurisdictions
  - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`: Community ID
  - `name TEXT NOT NULL`: Community name
  - `jurisdiction_type TEXT`: Type of jurisdiction (city, county, etc.)
  - `population INTEGER`: Population size
  - `economic_context TEXT`: Economic context information
  - `political_landscape TEXT`: Political landscape information
  - `budget_constraints TEXT`: Budget constraints information
  - `local_challenges TEXT`: Local challenges information
  - `key_stakeholders JSONB`: Key stakeholder information
  - `created_at TIMESTAMP WITH TIME ZONE`: When the community was created
  - `updated_at TIMESTAMP WITH TIME ZONE`: When the community was last updated

- **community_admins**: Manages administrator access for communities
  - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`: Admin record ID
  - `admin_id UUID REFERENCES auth.users(id)`: User ID of the admin
  - `community_id UUID REFERENCES public.communities(id)`: Community being administered
  - `created_at TIMESTAMP WITH TIME ZONE`: When the admin role was created
  - `UNIQUE(admin_id, community_id)`: Ensures a user is only an admin once per community

## Database Indexes

The following indexes were created to optimize query performance:

```sql
CREATE INDEX idx_traces_policy_type ON policy_aide.traces(policy_type);
CREATE INDEX idx_traces_created_at ON policy_aide.traces(created_at);
CREATE INDEX idx_spans_trace_id ON policy_aide.spans(trace_id);
CREATE INDEX idx_spans_agent_name ON policy_aide.spans(agent_name);
CREATE INDEX idx_spans_span_type ON policy_aide.spans(span_type);
```

## Row Level Security (RLS) Policies

Security policies were implemented to control access to data:

### `public.profiles`
- **Enable profile access control**: Ensures users can only access their own profile data
  - Policy: `auth.uid() = id`
  - Applied to all operations (SELECT, INSERT, UPDATE, DELETE)
  - Target roles: authenticated users

### `public.communities`
- **Community read access**: Allows all authenticated users to read community data
  - Policy: `true`
  - Applied to SELECT operations
  - Target roles: authenticated users

- **Community admin write access**: Restricts write operations to community administrators
  - Policy: `auth.uid() IN (SELECT admin_id FROM community_admins WHERE community_id = id)`
  - Applied to INSERT, UPDATE, DELETE operations
  - Target roles: authenticated users

### `policy_aide.traces`
- **Admin traces write access**: Restricts write access to system roles
  - Policy: `auth.role() = 'service_role'`
  - Applied to INSERT, UPDATE, DELETE operations
  - Target roles: service_role

- **User traces read access**: Allows users to read their own trace data
  - Policy: `auth.uid()::text = policy_query`
  - Applied to SELECT operations
  - Target roles: authenticated users

### `policy_aide.spans`
- **Admin spans write access**: Restricts write access to system roles
  - Policy: `auth.role() = 'service_role'`
  - Applied to INSERT, UPDATE, DELETE operations
  - Target roles: service_role

- **User spans read access**: Allows users to read spans related to their traces
  - Policy: `trace_id IN (SELECT trace_id FROM policy_aide.traces WHERE auth.uid()::text = policy_query)`
  - Applied to SELECT operations
  - Target roles: authenticated users

## Implementation Notes

1. The database is organized with separate schemas for different functional areas to allow for future expansion.

2. Row Level Security (RLS) is enabled on all tables to ensure proper access control.

3. The `policy_aide` schema is designed specifically for the PolicyAide trace data but is part of the broader CivicAide database.

4. JSON/JSONB columns are used for flexible data storage where schema might evolve over time.

5. The system is designed to store both local traces and references to OpenAI's trace data where available.

6. Database Connection: Due to IPv6 limitations on local networks, CivicAide uses Supabase's IPv4-compatible transaction pooler (Shared Pooler) connection. Environment configurations: user=postgres.lgsyjrdurhanlymmqndk host=aws-0-us-east-1.pooler.supabase.com port=6543 dbname=postgres password=YOUR_DATABASE_PASSWORD   Do not include brackets ([]) around values.

## Next Steps

1. **Code Integration**: Update the `CivicAideTraceProcessor` to save trace data to the Supabase database.

2. **User Management**: Implement user registration and profile management.

3. **Admin System**: Develop the administrative interface for managing community settings.

4. **Dashboard Updates**: Modify the trace dashboard to retrieve data from Supabase.

5. **Connection Pooling**: Monitor database performance and implement connection pooling if needed.

6. **Backup Strategy**: Set up regular database backups to prevent data loss.

7. **Migration Strategy**: Implement a proper migration system using Supabase migrations or a tool like Alembic.

## Conclusion

The database structure implemented in Supabase provides a solid foundation for the CivicAide platform, with particular emphasis on the PolicyAide tool's trace data storage needs. The schema design allows for future expansion while maintaining proper security controls through Row Level Security policies. This approach gives the project flexibility to grow while ensuring data security and integrity from the start.