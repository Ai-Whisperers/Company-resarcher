-- Company Researcher - PostgreSQL Schema
-- This file initializes the database with required tables

-- Research Tasks
CREATE TABLE IF NOT EXISTS research_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    market VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Research Results
CREATE TABLE IF NOT EXISTS research_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES research_tasks(id) ON DELETE CASCADE,
    section VARCHAR(100) NOT NULL,
    content TEXT,
    sources JSONB DEFAULT '[]'::jsonb,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Source Cache
CREATE TABLE IF NOT EXISTS source_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    content_hash VARCHAR(64),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Search Query Log
CREATE TABLE IF NOT EXISTS search_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    provider VARCHAR(50),
    result_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Usage Tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255),
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_research_tasks_status ON research_tasks(status);
CREATE INDEX IF NOT EXISTS idx_research_tasks_company ON research_tasks(company_name);
CREATE INDEX IF NOT EXISTS idx_research_results_task ON research_results(task_id);
CREATE INDEX IF NOT EXISTS idx_source_cache_url ON source_cache(url);
CREATE INDEX IF NOT EXISTS idx_source_cache_expires ON source_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_provider ON api_usage(provider);
CREATE INDEX IF NOT EXISTS idx_api_usage_date ON api_usage(created_at);

-- Full-text search on source content
CREATE INDEX IF NOT EXISTS idx_source_cache_content_fts
    ON source_cache USING GIN (to_tsvector('english', content));
