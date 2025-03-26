-- Enable Row-Level Security on policy_aide.spans and policy_aide.traces
ALTER TABLE policy_aide.spans ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_aide.traces ENABLE ROW LEVEL SECURITY;

-- Enable Row-Level Security on public tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.communities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.community_admins ENABLE ROW LEVEL SECURITY;

-- Create policies for policy_aide.spans
CREATE POLICY spans_read_policy ON policy_aide.spans
  FOR SELECT
  USING (auth.uid() IN (
    SELECT auth.uid() FROM policy_aide.traces
    WHERE policy_aide.traces.trace_id = policy_aide.spans.trace_id
  ));

CREATE POLICY spans_insert_policy ON policy_aide.spans
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Create policies for policy_aide.traces
CREATE POLICY traces_read_policy ON policy_aide.traces
  FOR SELECT
  USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY traces_insert_policy ON policy_aide.traces
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Create policies for public.profiles
CREATE POLICY profiles_read_policy ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY profiles_insert_policy ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY profiles_update_policy ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id);

-- Create policies for public.communities
CREATE POLICY communities_read_policy ON public.communities
  FOR SELECT
  USING (true);

CREATE POLICY communities_admin_policy ON public.communities
  FOR ALL
  USING (auth.uid() IN (
    SELECT admin_id FROM public.community_admins
    WHERE community_id = id
  ));

-- Create policies for public.community_admins
CREATE POLICY community_admins_read_policy ON public.community_admins
  FOR SELECT
  USING (auth.uid() = admin_id OR auth.role() = 'service_role');

CREATE POLICY community_admins_insert_policy ON public.community_admins
  FOR INSERT
  WITH CHECK (auth.role() = 'service_role'); 