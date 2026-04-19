-- =============================================================================
-- Project Sentinel — Supabase Tables
-- Run this entire script in the Supabase SQL Editor
-- =============================================================================

-- Research Papers: every paper the system discovers
CREATE TABLE research_papers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    abstract TEXT,
    publication_date DATE,
    citation_count INTEGER DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'semantic_scholar',
    source_id TEXT,
    url TEXT,
    pdf_url TEXT,
    topic_tags TEXT[] DEFAULT '{}',
    relevance_score NUMERIC(3,2),
    status TEXT NOT NULL DEFAULT 'discovered'
        CHECK (status IN ('discovered', 'abstract_reviewed', 'queued_for_deep_review', 'reviewed', 'archived')),
    discovered_at TIMESTAMPTZ DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    notes TEXT
);

CREATE INDEX idx_research_papers_status ON research_papers (status);
CREATE INDEX idx_research_papers_source ON research_papers (source, source_id);

-- Research Topics: standing list of research interests
CREATE TABLE research_topics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    topic TEXT NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 3),
    created_by TEXT NOT NULL DEFAULT 'claude_code',
    active BOOLEAN DEFAULT true,
    last_searched TIMESTAMPTZ,
    paper_count INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Research Questions: actual questions driving the research program
CREATE TABLE research_questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question TEXT NOT NULL,
    context TEXT,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'partially_answered', 'answered', 'abandoned')),
    evidence_count INTEGER DEFAULT 0,
    current_best_answer TEXT,
    created_by TEXT NOT NULL DEFAULT 'claude_code',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Research Evidence: links papers to questions
CREATE TABLE research_evidence (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question_id UUID NOT NULL REFERENCES research_questions(id),
    paper_id UUID REFERENCES research_papers(id),
    source_type TEXT,
    source_id TEXT,
    relevance_score NUMERIC(3,2),
    key_finding TEXT NOT NULL,
    supports_or_challenges TEXT CHECK (supports_or_challenges IN ('supports', 'challenges', 'neutral')),
    added_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_research_evidence_question ON research_evidence (question_id);

-- Data Sources: catalog of discovered APIs and data sources
CREATE TABLE data_sources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    auth_required TEXT NOT NULL DEFAULT 'none'
        CHECK (auth_required IN ('none', 'free_key', 'paid_key', 'subscription')),
    data_types TEXT[] DEFAULT '{}',
    rate_limits TEXT,
    quality_assessment TEXT,
    status TEXT NOT NULL DEFAULT 'discovered'
        CHECK (status IN ('discovered', 'tested', 'active', 'rejected', 'deprecated')),
    discovered_at TIMESTAMPTZ DEFAULT now(),
    tested_at TIMESTAMPTZ,
    notes TEXT
);

-- Experiments: test agent results and lessons
CREATE TABLE experiments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    experiment_name TEXT NOT NULL,
    hypothesis TEXT,
    data_source TEXT,
    approach TEXT,
    result_summary TEXT,
    output_sample JSONB,
    success BOOLEAN,
    lessons_learned TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Agent Outputs: structured output from every agent execution
CREATE TABLE agent_outputs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_name TEXT NOT NULL,
    output_type TEXT,
    output_summary TEXT,
    output_data JSONB,
    telegram_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_agent_outputs_agent ON agent_outputs (agent_name, created_at DESC);

-- Environmental Observations: structured data from monitoring agents
CREATE TABLE environmental_observations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    observation_type TEXT NOT NULL
        CHECK (observation_type IN ('air_quality', 'earthquake', 'tide', 'weather', 'pesticide', 'uv', 'water_quality', 'fire', 'other')),
    value NUMERIC,
    unit TEXT,
    location TEXT DEFAULT 'CA',
    source TEXT NOT NULL,
    details JSONB,
    observed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_env_obs_type ON environmental_observations (observation_type, observed_at DESC);

-- Daily Digests: synthesized briefings for historical search
CREATE TABLE daily_digests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    digest_type TEXT NOT NULL,
    content TEXT NOT NULL,
    sources_used TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_daily_digests_type ON daily_digests (digest_type, created_at DESC);

-- Enable RLS on all new tables with permissive policies for service role
ALTER TABLE research_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE environmental_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_digests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON research_papers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON research_topics FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON research_questions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON research_evidence FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON data_sources FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON experiments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON agent_outputs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON environmental_observations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON daily_digests FOR ALL USING (true) WITH CHECK (true);

-- Verify all tables created
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
