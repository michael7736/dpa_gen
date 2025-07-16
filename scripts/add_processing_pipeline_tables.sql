-- 添加文档处理管道相关表

-- 1. 创建处理管道表
CREATE TABLE IF NOT EXISTS processing_pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 管道状态
    current_stage VARCHAR(50),
    overall_progress FLOAT DEFAULT 0.0,
    interrupted BOOLEAN DEFAULT FALSE,
    completed BOOLEAN DEFAULT FALSE,
    can_resume BOOLEAN DEFAULT TRUE,
    
    -- 处理选项
    processing_options JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 索引
    CONSTRAINT fk_pipeline_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_pipeline_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_pipelines_document_id ON processing_pipelines(document_id);
CREATE INDEX IF NOT EXISTS idx_pipelines_user_id ON processing_pipelines(user_id);
CREATE INDEX IF NOT EXISTS idx_pipelines_current_stage ON processing_pipelines(current_stage);
CREATE INDEX IF NOT EXISTS idx_pipelines_completed ON processing_pipelines(completed);

-- 2. 创建管道阶段表
CREATE TABLE IF NOT EXISTS pipeline_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID NOT NULL REFERENCES processing_pipelines(id) ON DELETE CASCADE,
    
    -- 阶段信息
    stage_type VARCHAR(50) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    
    -- 执行信息
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration FLOAT,
    estimated_time INTEGER,
    
    -- 状态信息
    message TEXT,
    can_interrupt BOOLEAN DEFAULT TRUE,
    
    -- 结果和错误
    result JSONB,
    error TEXT,
    error_details JSONB,
    
    -- 配置
    config JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT fk_stage_pipeline FOREIGN KEY (pipeline_id) REFERENCES processing_pipelines(id) ON DELETE CASCADE,
    CONSTRAINT check_progress CHECK (progress >= 0 AND progress <= 100)
);

CREATE INDEX IF NOT EXISTS idx_stages_pipeline_id ON pipeline_stages(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_stages_status ON pipeline_stages(status);
CREATE INDEX IF NOT EXISTS idx_stages_stage_type ON pipeline_stages(stage_type);

-- 3. 创建处理结果表
CREATE TABLE IF NOT EXISTS processing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES processing_pipelines(id) ON DELETE CASCADE,
    stage_id UUID NOT NULL REFERENCES pipeline_stages(id) ON DELETE CASCADE,
    
    -- 结果信息
    result_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) DEFAULT 'json',
    
    -- 存储位置
    storage_path VARCHAR(500),
    inline_content JSONB,
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    size INTEGER,
    checksum VARCHAR(64),
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- 约束
    CONSTRAINT fk_result_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_result_pipeline FOREIGN KEY (pipeline_id) REFERENCES processing_pipelines(id) ON DELETE CASCADE,
    CONSTRAINT fk_result_stage FOREIGN KEY (stage_id) REFERENCES pipeline_stages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_results_document_id ON processing_results(document_id);
CREATE INDEX IF NOT EXISTS idx_results_pipeline_id ON processing_results(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_results_result_type ON processing_results(result_type);

-- 4. 更新文档表状态枚举（如果需要）
-- 注意：这可能需要特殊处理，因为涉及枚举类型的修改
-- 以下是一种方法：

-- 首先检查是否需要更新枚举
DO $$
BEGIN
    -- 检查新的状态值是否存在
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_enum 
        WHERE enumlabel = 'uploaded' 
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = 'processingstatus'
        )
    ) THEN
        -- 添加新的枚举值
        ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'uploaded' BEFORE 'pending';
        ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'summarizing' AFTER 'processing';
        ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'summarized' AFTER 'summarizing';
        ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'indexing' AFTER 'summarized';
        ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'indexed' AFTER 'indexing';
        ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'analyzing' AFTER 'indexed';
        ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'analyzed' AFTER 'analyzing';
    END IF;
END $$;

-- 5. 更新触发器以维护updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_processing_pipelines_updated_at BEFORE UPDATE
    ON processing_pipelines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_stages_updated_at BEFORE UPDATE
    ON pipeline_stages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();