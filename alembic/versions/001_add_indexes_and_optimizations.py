"""添加索引和优化

Revision ID: 001
Revises: 
Create Date: 2025-07-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加索引和优化"""
    
    # 1. 为 users 表添加索引
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # 2. 为 projects 表添加索引
    op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_project_type', 'projects', ['project_type'])
    op.create_index('idx_projects_created_at', 'projects', ['created_at'])
    # 复合索引：常用的查询组合
    op.create_index('idx_projects_owner_status', 'projects', ['owner_id', 'status'])
    
    # 3. 为 documents 表添加索引
    op.create_index('idx_documents_project_id', 'documents', ['project_id'])
    op.create_index('idx_documents_file_hash', 'documents', ['file_hash'])
    op.create_index('idx_documents_processing_status', 'documents', ['processing_status'])
    op.create_index('idx_documents_document_type', 'documents', ['document_type'])
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    # 复合索引：项目内文档查询
    op.create_index('idx_documents_project_status', 'documents', ['project_id', 'processing_status'])
    # 全文搜索索引（PostgreSQL特有）
    op.execute("""
        CREATE INDEX idx_documents_title_fts ON documents 
        USING gin(to_tsvector('english', title))
    """)
    
    # 4. 为 chunks 表添加索引
    op.create_index('idx_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('idx_chunks_vector_id', 'chunks', ['vector_id'])
    op.create_index('idx_chunks_chunk_index', 'chunks', ['chunk_index'])
    op.create_index('idx_chunks_content_hash', 'chunks', ['content_hash'])
    # 复合索引：文档内块查询
    op.create_index('idx_chunks_doc_index', 'chunks', ['document_id', 'chunk_index'])
    
    # 5. 为 conversations 表添加索引
    op.create_index('idx_conversations_project_id', 'conversations', ['project_id'])
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_status', 'conversations', ['status'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    # 复合索引：用户在项目中的对话
    op.create_index('idx_conversations_user_project', 'conversations', ['user_id', 'project_id'])
    
    # 6. 添加性能优化字段
    
    # 为 documents 表添加统计字段（避免重复计算）
    op.add_column('documents', sa.Column('chunk_count', sa.Integer(), default=0))
    op.add_column('documents', sa.Column('total_tokens', sa.Integer(), default=0))
    op.add_column('documents', sa.Column('processing_time_seconds', sa.Float()))
    
    # 为 projects 表添加统计字段
    op.add_column('projects', sa.Column('document_count', sa.Integer(), default=0))
    op.add_column('projects', sa.Column('total_chunks', sa.Integer(), default=0))
    op.add_column('projects', sa.Column('last_accessed_at', sa.DateTime(timezone=True)))
    
    # 为 users 表添加使用统计
    op.add_column('users', sa.Column('project_count', sa.Integer(), default=0))
    op.add_column('users', sa.Column('total_documents', sa.Integer(), default=0))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True)))
    op.add_column('users', sa.Column('login_count', sa.Integer(), default=0))
    
    # 7. 创建物化视图用于常用统计（PostgreSQL特有）
    op.execute("""
        CREATE MATERIALIZED VIEW project_statistics AS
        SELECT 
            p.id as project_id,
            p.owner_id,
            COUNT(DISTINCT d.id) as document_count,
            COUNT(DISTINCT c.id) as chunk_count,
            COALESCE(SUM(d.total_tokens), 0) as total_tokens,
            MAX(d.created_at) as last_document_at
        FROM projects p
        LEFT JOIN documents d ON p.id = d.project_id
        LEFT JOIN chunks c ON d.id = c.document_id
        GROUP BY p.id, p.owner_id
    """)
    
    # 为物化视图创建索引
    op.execute("""
        CREATE INDEX idx_project_stats_project_id ON project_statistics(project_id);
        CREATE INDEX idx_project_stats_owner_id ON project_statistics(owner_id);
    """)
    
    # 8. 添加触发器自动更新统计字段
    
    # 文档计数触发器
    op.execute("""
        CREATE OR REPLACE FUNCTION update_project_document_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE projects SET document_count = document_count + 1 
                WHERE id = NEW.project_id;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE projects SET document_count = document_count - 1 
                WHERE id = OLD.project_id;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_update_project_document_count
        AFTER INSERT OR DELETE ON documents
        FOR EACH ROW EXECUTE FUNCTION update_project_document_count();
    """)
    
    # 块计数触发器
    op.execute("""
        CREATE OR REPLACE FUNCTION update_document_chunk_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE documents SET chunk_count = chunk_count + 1 
                WHERE id = NEW.document_id;
                UPDATE projects SET total_chunks = total_chunks + 1
                WHERE id = (SELECT project_id FROM documents WHERE id = NEW.document_id);
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE documents SET chunk_count = chunk_count - 1 
                WHERE id = OLD.document_id;
                UPDATE projects SET total_chunks = total_chunks - 1
                WHERE id = (SELECT project_id FROM documents WHERE id = OLD.document_id);
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_update_chunk_counts
        AFTER INSERT OR DELETE ON chunks
        FOR EACH ROW EXECUTE FUNCTION update_document_chunk_count();
    """)


def downgrade() -> None:
    """回滚变更"""
    
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS trg_update_chunk_counts ON chunks")
    op.execute("DROP TRIGGER IF EXISTS trg_update_project_document_count ON documents")
    op.execute("DROP FUNCTION IF EXISTS update_document_chunk_count()")
    op.execute("DROP FUNCTION IF EXISTS update_project_document_count()")
    
    # 删除物化视图
    op.execute("DROP MATERIALIZED VIEW IF EXISTS project_statistics")
    
    # 删除添加的列
    op.drop_column('users', 'login_count')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'total_documents')
    op.drop_column('users', 'project_count')
    
    op.drop_column('projects', 'last_accessed_at')
    op.drop_column('projects', 'total_chunks')
    op.drop_column('projects', 'document_count')
    
    op.drop_column('documents', 'processing_time_seconds')
    op.drop_column('documents', 'total_tokens')
    op.drop_column('documents', 'chunk_count')
    
    # 删除索引
    op.drop_index('idx_conversations_user_project', 'conversations')
    op.drop_index('idx_conversations_created_at', 'conversations')
    op.drop_index('idx_conversations_status', 'conversations')
    op.drop_index('idx_conversations_user_id', 'conversations')
    op.drop_index('idx_conversations_project_id', 'conversations')
    
    op.drop_index('idx_chunks_doc_index', 'chunks')
    op.drop_index('idx_chunks_content_hash', 'chunks')
    op.drop_index('idx_chunks_chunk_index', 'chunks')
    op.drop_index('idx_chunks_vector_id', 'chunks')
    op.drop_index('idx_chunks_document_id', 'chunks')
    
    op.execute("DROP INDEX IF EXISTS idx_documents_title_fts")
    op.drop_index('idx_documents_project_status', 'documents')
    op.drop_index('idx_documents_created_at', 'documents')
    op.drop_index('idx_documents_document_type', 'documents')
    op.drop_index('idx_documents_processing_status', 'documents')
    op.drop_index('idx_documents_file_hash', 'documents')
    op.drop_index('idx_documents_project_id', 'documents')
    
    op.drop_index('idx_projects_owner_status', 'projects')
    op.drop_index('idx_projects_created_at', 'projects')
    op.drop_index('idx_projects_project_type', 'projects')
    op.drop_index('idx_projects_status', 'projects')
    op.drop_index('idx_projects_owner_id', 'projects')
    
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_users_email', 'users')