-- AAG元数据Schema v2.0创建脚本

-- 创建文档元数据v2表
CREATE TABLE IF NOT EXISTS document_metadata_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    version INTEGER NOT NULL DEFAULT 1,
    
    -- 基础信息
    skim_summary JSONB,
    document_type VARCHAR(50),
    quality_score FLOAT,
    target_audience TEXT[],
    
    -- 分析状态
    analysis_status VARCHAR(50) DEFAULT 'pending',
    analysis_depth VARCHAR(50) DEFAULT 'basic',
    last_analysis_at TIMESTAMP,
    
    -- 分析计划
    analysis_plan JSONB,
    completed_steps TEXT[],
    
    -- 统计信息
    total_analyses INTEGER DEFAULT 0,
    total_artifacts INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    
    -- 扩展字段
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
    
    -- 内容
    content JSONB NOT NULL,
    summary TEXT,
    
    -- 执行信息
    execution_time_seconds INTEGER,
    token_usage INTEGER,
    model_used VARCHAR(100),
    
    -- 用户干预
    user_corrections JSONB DEFAULT '[]',
    is_user_approved BOOLEAN DEFAULT FALSE,
    
    -- 版本控制
    version INTEGER NOT NULL DEFAULT 1,
    parent_artifact_id UUID REFERENCES analysis_artifacts(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 创建分析任务表
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    
    -- 任务信息
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    
    -- 执行计划
    execution_plan JSONB NOT NULL,
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER NOT NULL,
    
    -- 执行状态
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- 结果引用
    artifact_ids UUID[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_artifacts_document_type ON analysis_artifacts(document_id, analysis_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_created_at ON analysis_artifacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON analysis_tasks(status, priority DESC);

-- 为documents表添加aag相关字段
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='has_skim_summary') THEN
        ALTER TABLE documents ADD COLUMN has_skim_summary BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='has_knowledge_graph') THEN
        ALTER TABLE documents ADD COLUMN has_knowledge_graph BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='last_deep_analysis_at') THEN
        ALTER TABLE documents ADD COLUMN last_deep_analysis_at TIMESTAMP;
    END IF;
END $$;

-- 添加注释
COMMENT ON TABLE document_metadata_v2 IS 'AAG文档元数据表v2';
COMMENT ON TABLE analysis_artifacts IS 'AAG分析物料存储表';
COMMENT ON TABLE analysis_tasks IS 'AAG分析任务管理表';

COMMENT ON COLUMN document_metadata_v2.skim_summary IS '快速略读结果';
COMMENT ON COLUMN document_metadata_v2.quality_score IS '文档质量评分(0-1)';
COMMENT ON COLUMN document_metadata_v2.analysis_status IS '分析状态: pending|processing|completed|failed';
COMMENT ON COLUMN document_metadata_v2.analysis_depth IS '分析深度: basic|standard|deep|expert|comprehensive';

COMMENT ON COLUMN analysis_artifacts.analysis_type IS '分析类型: skim|summary|outline|knowledge_graph|evidence_chain等';
COMMENT ON COLUMN analysis_artifacts.content IS '分析结果的JSON内容';
COMMENT ON COLUMN analysis_artifacts.user_corrections IS '用户修正历史';

COMMENT ON COLUMN analysis_tasks.task_type IS '任务类型: comprehensive_analysis|quick_skim|deep_dive等';
COMMENT ON COLUMN analysis_tasks.status IS '任务状态: pending|running|paused|completed|failed|cancelled';
COMMENT ON COLUMN analysis_tasks.execution_plan IS '任务执行计划JSON';