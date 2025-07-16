-- AAG元数据Schema v2.0创建脚本（简化版）

-- 创建文档元数据v2表
CREATE TABLE IF NOT EXISTS document_metadata_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    version INTEGER NOT NULL DEFAULT 1,
    skim_summary JSONB,
    document_type VARCHAR(50),
    quality_score FLOAT,
    target_audience TEXT[],
    analysis_status VARCHAR(50) DEFAULT 'pending',
    analysis_depth VARCHAR(50) DEFAULT 'basic',
    last_analysis_at TIMESTAMP,
    analysis_plan JSONB,
    completed_steps TEXT[],
    total_analyses INTEGER DEFAULT 0,
    total_artifacts INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    ext JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, version)
);

-- 创建分析物料表
CREATE TABLE IF NOT EXISTS analysis_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    analysis_type VARCHAR(100) NOT NULL,
    depth_level VARCHAR(50),
    content JSONB NOT NULL,
    summary TEXT,
    execution_time_seconds INTEGER,
    token_usage INTEGER,
    model_used VARCHAR(100),
    user_corrections JSONB DEFAULT '[]',
    is_user_approved BOOLEAN DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1,
    parent_artifact_id UUID REFERENCES analysis_artifacts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 创建分析任务表
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    execution_plan JSONB NOT NULL,
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    artifact_ids UUID[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_artifacts_document_type ON analysis_artifacts(document_id, analysis_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_created_at ON analysis_artifacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON analysis_tasks(status, priority DESC);