-- 创建文档分析表
-- 用于存储高级文档深度分析的结果

-- 确保UUID扩展存在
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建文档分析表
CREATE TABLE IF NOT EXISTS document_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    
    -- 分析配置
    analysis_depth VARCHAR(50) DEFAULT 'standard',
    analysis_goal TEXT,
    
    -- 状态跟踪
    status VARCHAR(50) DEFAULT 'pending',
    current_stage VARCHAR(100),
    progress FLOAT DEFAULT 0.0,
    error_message TEXT,
    
    -- 时间记录
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_seconds FLOAT,
    
    -- 结果存储
    executive_summary TEXT,
    key_insights JSONB,
    recommendations JSONB,
    quality_score FLOAT,
    
    -- 详细结果（JSON格式）
    detailed_report JSONB,
    visualization_data JSONB,
    action_plan JSONB,
    
    -- 索引
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents(id),
    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 创建索引以提高查询性能
CREATE INDEX idx_analyses_document_id ON document_analyses(document_id);
CREATE INDEX idx_analyses_project_id ON document_analyses(project_id);
CREATE INDEX idx_analyses_user_id ON document_analyses(user_id);
CREATE INDEX idx_analyses_status ON document_analyses(status);
CREATE INDEX idx_analyses_created_at ON document_analyses(created_at DESC);

-- 创建分析状态枚举类型（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'analysis_status_enum') THEN
        CREATE TYPE analysis_status_enum AS ENUM (
            'pending',
            'running',
            'completed',
            'failed',
            'cancelled'
        );
    END IF;
END$$;

-- 创建分析深度枚举类型（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'analysis_depth_enum') THEN
        CREATE TYPE analysis_depth_enum AS ENUM (
            'basic',
            'standard',
            'deep',
            'expert',
            'comprehensive'
        );
    END IF;
END$$;

-- 创建分析阶段枚举类型（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'analysis_stage_enum') THEN
        CREATE TYPE analysis_stage_enum AS ENUM (
            'preparation',
            'macro_understanding',
            'deep_exploration',
            'critical_analysis',
            'knowledge_integration',
            'output_generation'
        );
    END IF;
END$$;

-- 添加触发器自动更新时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 如果表已存在但没有updated_at列，添加它
ALTER TABLE document_analyses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- 创建触发器
DROP TRIGGER IF EXISTS update_document_analyses_updated_at ON document_analyses;
CREATE TRIGGER update_document_analyses_updated_at 
    BEFORE UPDATE ON document_analyses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 添加注释
COMMENT ON TABLE document_analyses IS '文档深度分析记录表';
COMMENT ON COLUMN document_analyses.id IS '分析记录唯一标识';
COMMENT ON COLUMN document_analyses.document_id IS '关联的文档ID';
COMMENT ON COLUMN document_analyses.project_id IS '关联的项目ID';
COMMENT ON COLUMN document_analyses.user_id IS '执行分析的用户ID';
COMMENT ON COLUMN document_analyses.analysis_depth IS '分析深度级别：basic/standard/deep/expert/comprehensive';
COMMENT ON COLUMN document_analyses.analysis_goal IS '用户指定的分析目标';
COMMENT ON COLUMN document_analyses.status IS '分析状态：pending/running/completed/failed/cancelled';
COMMENT ON COLUMN document_analyses.current_stage IS '当前分析阶段';
COMMENT ON COLUMN document_analyses.progress IS '分析进度百分比';
COMMENT ON COLUMN document_analyses.error_message IS '错误信息（如果失败）';
COMMENT ON COLUMN document_analyses.executive_summary IS '执行摘要';
COMMENT ON COLUMN document_analyses.key_insights IS '关键洞察（JSON数组）';
COMMENT ON COLUMN document_analyses.recommendations IS '建议列表（JSON数组）';
COMMENT ON COLUMN document_analyses.quality_score IS '文档质量评分（0-1）';
COMMENT ON COLUMN document_analyses.detailed_report IS '详细分析报告（JSON）';
COMMENT ON COLUMN document_analyses.visualization_data IS '可视化数据（JSON）';
COMMENT ON COLUMN document_analyses.action_plan IS '行动计划（JSON）';

-- 输出成功信息
SELECT 'Document analyses table created successfully' AS message;