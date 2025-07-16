-- 为projects表添加is_default字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;

-- 为is_default字段创建索引
CREATE INDEX IF NOT EXISTS idx_projects_is_default ON projects(is_default);

-- 确保每个用户只有一个默认项目的约束（使用部分索引）
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_default_project_per_user 
ON projects(user_id) 
WHERE is_default = TRUE;