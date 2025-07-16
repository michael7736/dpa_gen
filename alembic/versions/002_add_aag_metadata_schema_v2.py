"""Add AAG metadata schema v2

Revision ID: 002_aag_metadata_v2
Revises: 001_add_indexes_and_optimizations
Create Date: 2024-01-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_aag_metadata_v2'
down_revision = '001_add_indexes_and_optimizations'
branch_labels = None
depends_on = None


def upgrade():
    # 创建文档元数据v2表
    op.create_table('document_metadata_v2',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        
        # 基础信息
        sa.Column('skim_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('document_type', sa.String(50), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('target_audience', postgresql.ARRAY(sa.Text()), nullable=True),
        
        # 分析状态
        sa.Column('analysis_status', sa.String(50), nullable=True, server_default='pending'),
        sa.Column('analysis_depth', sa.String(50), nullable=True, server_default='basic'),
        sa.Column('last_analysis_at', sa.TIMESTAMP(), nullable=True),
        
        # 分析计划
        sa.Column('analysis_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('completed_steps', postgresql.ARRAY(sa.Text()), nullable=True),
        
        # 统计信息
        sa.Column('total_analyses', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_artifacts', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_tokens_used', sa.Integer(), nullable=True, server_default='0'),
        
        # 扩展字段
        sa.Column('ext', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.UniqueConstraint('document_id', 'version')
    )
    
    # 创建分析物料表
    op.create_table('analysis_artifacts',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('analysis_type', sa.String(100), nullable=False),
        sa.Column('depth_level', sa.String(50), nullable=True),
        
        # 内容
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        
        # 执行信息
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('token_usage', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        
        # 用户干预
        sa.Column('user_corrections', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('is_user_approved', sa.Boolean(), nullable=True, server_default='false'),
        
        # 版本控制
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_artifact_id', sa.UUID(), nullable=True),
        
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(100), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['parent_artifact_id'], ['analysis_artifacts.id'], )
    )
    
    # 创建分析任务表
    op.create_table('analysis_tasks',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', sa.UUID(), nullable=False),
        
        # 任务信息
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='5'),
        
        # 执行计划
        sa.Column('execution_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        
        # 执行状态
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # 结果引用
        sa.Column('artifact_ids', postgresql.ARRAY(sa.UUID()), nullable=True),
        
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(100), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], )
    )
    
    # 创建索引
    op.create_index('idx_artifacts_document_type', 'analysis_artifacts', ['document_id', 'analysis_type'])
    op.create_index('idx_artifacts_created_at', 'analysis_artifacts', ['created_at'])
    op.create_index('idx_tasks_status', 'analysis_tasks', ['status', 'priority'])
    
    # 为documents表添加aag相关字段（如果不存在）
    try:
        op.add_column('documents', sa.Column('has_skim_summary', sa.Boolean(), nullable=True, server_default='false'))
        op.add_column('documents', sa.Column('has_knowledge_graph', sa.Boolean(), nullable=True, server_default='false'))
        op.add_column('documents', sa.Column('last_deep_analysis_at', sa.TIMESTAMP(), nullable=True))
    except:
        # 列可能已存在
        pass


def downgrade():
    # 删除索引
    op.drop_index('idx_tasks_status', table_name='analysis_tasks')
    op.drop_index('idx_artifacts_created_at', table_name='analysis_artifacts')
    op.drop_index('idx_artifacts_document_type', table_name='analysis_artifacts')
    
    # 删除表
    op.drop_table('analysis_tasks')
    op.drop_table('analysis_artifacts')
    op.drop_table('document_metadata_v2')
    
    # 删除documents表的列（如果存在）
    try:
        op.drop_column('documents', 'last_deep_analysis_at')
        op.drop_column('documents', 'has_knowledge_graph')
        op.drop_column('documents', 'has_skim_summary')
    except:
        pass