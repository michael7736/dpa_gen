"""添加对话历史表

Revision ID: 77e7cdf667d2
Revises: 001
Create Date: 2025-07-07 09:00:59.050301

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '77e7cdf667d2'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建对话表
    op.create_table('conversations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_project_id'), 'conversations', ['project_id'], unique=False)
    op.create_index(op.f('ix_conversations_title'), 'conversations', ['title'], unique=False)
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    
    # 创建消息表
    op.create_table('messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', name='messagerole'), nullable=False),
        sa.Column('message_type', sa.Enum('TEXT', 'QUERY', 'ANALYSIS', 'SUMMARY', 'COMPARISON', 'RISK_ASSESSMENT', name='messagetype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('sources', sa.Text(), nullable=True),
        sa.Column('citations', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('message_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_role'), 'messages', ['role'], unique=False)
    op.create_index(op.f('ix_messages_message_type'), 'messages', ['message_type'], unique=False)
    op.create_index(op.f('ix_messages_sequence_number'), 'messages', ['sequence_number'], unique=False)


def downgrade() -> None:
    # 删除消息表
    op.drop_index(op.f('ix_messages_sequence_number'), table_name='messages')
    op.drop_index(op.f('ix_messages_message_type'), table_name='messages')
    op.drop_index(op.f('ix_messages_role'), table_name='messages')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_table('messages')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS messagetype')
    op.execute('DROP TYPE IF EXISTS messagerole')
    
    # 删除对话表
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_title'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_project_id'), table_name='conversations')
    op.drop_table('conversations')
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), autoincrement=False, nullable=False, comment='分析记录唯一标识'),
    sa.Column('document_id', sa.UUID(), autoincrement=False, nullable=False, comment='关联的文档ID'),
    sa.Column('project_id', sa.UUID(), autoincrement=False, nullable=False, comment='关联的项目ID'),
    sa.Column('user_id', sa.VARCHAR(length=255), autoincrement=False, nullable=False, comment='执行分析的用户ID'),
    sa.Column('analysis_depth', sa.VARCHAR(length=50), server_default=sa.text("'standard'::character varying"), autoincrement=False, nullable=True, comment='分析深度级别：basic/standard/deep/expert/comprehensive'),
    sa.Column('analysis_goal', sa.TEXT(), autoincrement=False, nullable=True, comment='用户指定的分析目标'),
    sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'pending'::character varying"), autoincrement=False, nullable=True, comment='分析状态：pending/running/completed/failed/cancelled'),
    sa.Column('current_stage', sa.VARCHAR(length=100), autoincrement=False, nullable=True, comment='当前分析阶段'),
    sa.Column('progress', sa.DOUBLE_PRECISION(precision=53), server_default=sa.text('0.0'), autoincrement=False, nullable=True, comment='分析进度百分比'),
    sa.Column('error_message', sa.TEXT(), autoincrement=False, nullable=True, comment='错误信息（如果失败）'),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('processing_time_seconds', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('executive_summary', sa.TEXT(), autoincrement=False, nullable=True, comment='执行摘要'),
    sa.Column('key_insights', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='关键洞察（JSON数组）'),
    sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='建议列表（JSON数组）'),
    sa.Column('quality_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True, comment='文档质量评分（0-1）'),
    sa.Column('detailed_report', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='详细分析报告（JSON）'),
    sa.Column('visualization_data', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='可视化数据（JSON）'),
    sa.Column('action_plan', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='行动计划（JSON）'),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('document_analyses_document_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_document')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('document_analyses_project_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project')),
    sa.PrimaryKeyConstraint('id', name=op.f('document_analyses_pkey')),
    comment='文档深度分析记录表'
    )
    op.create_index(op.f('idx_analyses_user_id'), 'document_analyses', ['user_id'], unique=False)
    op.create_index(op.f('idx_analyses_status'), 'document_analyses', ['status'], unique=False)
    op.create_index(op.f('idx_analyses_project_id'), 'document_analyses', ['project_id'], unique=False)
    op.create_index(op.f('idx_analyses_document_id'), 'document_analyses', ['document_id'], unique=False)
    op.create_index(op.f('idx_analyses_created_at'), 'document_analyses', [sa.literal_column('created_at DESC')], unique=False)
    op.create_table('memories',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('project_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('memory_type', postgresql.ENUM('SEMANTIC', 'EPISODIC', 'WORKING', 'DECLARATIVE', 'PROCEDURAL', name='memorytype'), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('embedding', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'ARCHIVED', 'DELETED', name='memorystatus'), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('memories_pkey'))
    )
    op.create_index(op.f('ix_memories_user_id'), 'memories', ['user_id'], unique=False)
    op.create_index(op.f('ix_memories_project_id'), 'memories', ['project_id'], unique=False)
    op.create_table('user_memories',
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('language_preference', sa.VARCHAR(length=10), autoincrement=False, nullable=True, comment='语言偏好'),
    sa.Column('response_style', sa.VARCHAR(length=50), autoincrement=False, nullable=True, comment='回答风格'),
    sa.Column('expertise_level', sa.VARCHAR(length=20), autoincrement=False, nullable=True, comment='专业水平'),
    sa.Column('preferred_chunk_size', sa.INTEGER(), autoincrement=False, nullable=True, comment='偏好的结果数量'),
    sa.Column('detail_level', sa.VARCHAR(length=20), autoincrement=False, nullable=True, comment='详细程度'),
    sa.Column('include_sources', sa.BOOLEAN(), autoincrement=False, nullable=True, comment='是否包含来源'),
    sa.Column('interests', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='兴趣领域'),
    sa.Column('expertise_areas', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='专长领域'),
    sa.Column('avoided_topics', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='避免的主题'),
    sa.Column('active_hours', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='活跃时段'),
    sa.Column('query_patterns', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='查询模式'),
    sa.Column('favorite_projects', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='常用项目'),
    sa.Column('custom_prompts', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='自定义提示词'),
    sa.Column('shortcuts', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='快捷方式'),
    sa.Column('ui_preferences', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='界面偏好'),
    sa.Column('metadata_info', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('deleted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('user_memories_user_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('user_memories_pkey')),
    sa.UniqueConstraint('user_id', name=op.f('user_memories_user_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('conversation_memories',
    sa.Column('conversation_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('turn_number', sa.INTEGER(), autoincrement=False, nullable=True, comment='对话轮次'),
    sa.Column('user_message', sa.TEXT(), autoincrement=False, nullable=True, comment='用户消息'),
    sa.Column('assistant_response', sa.TEXT(), autoincrement=False, nullable=True, comment='助手回复'),
    sa.Column('entities_mentioned', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='提到的实体'),
    sa.Column('topics_discussed', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='讨论的主题'),
    sa.Column('decisions_made', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='做出的决定'),
    sa.Column('is_important', sa.BOOLEAN(), autoincrement=False, nullable=True, comment='是否重要'),
    sa.Column('importance_reason', sa.TEXT(), autoincrement=False, nullable=True, comment='重要原因'),
    sa.Column('referenced_documents', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='引用的文档'),
    sa.Column('generated_tasks', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='生成的任务'),
    sa.Column('metadata_info', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('deleted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('conversation_memories_conversation_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('conversation_memories_pkey'))
    )
    op.create_index(op.f('ix_conversation_memories_conversation_id'), 'conversation_memories', ['conversation_id'], unique=False)
    op.create_table('document_metadata',
    sa.Column('document_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('project_id', sa.UUID(), autoincrement=False, nullable=True, comment='所属项目'),
    sa.Column('directory_path', sa.VARCHAR(), autoincrement=False, nullable=True, comment='所在目录路径'),
    sa.Column('upstream_references', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='参考文献-上游'),
    sa.Column('downstream_citations', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='被引用文献-下游'),
    sa.Column('source_type', sa.VARCHAR(length=50), autoincrement=False, nullable=True, comment='文档来源类型'),
    sa.Column('source_url', sa.TEXT(), autoincrement=False, nullable=True, comment='原始URL（如果是网络来源）'),
    sa.Column('source_metadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='来源相关元数据'),
    sa.Column('confidence_stars', sa.INTEGER(), autoincrement=False, nullable=True, comment='置信度星级 1-5'),
    sa.Column('confidence_level', sa.VARCHAR(length=50), autoincrement=False, nullable=True, comment='置信度等级'),
    sa.Column('confidence_notes', sa.TEXT(), autoincrement=False, nullable=True, comment='置信度评级说明'),
    sa.Column('publication_date', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True, comment='发表时间'),
    sa.Column('publication_year_month', sa.VARCHAR(length=20), autoincrement=False, nullable=True, comment='发表年月 YYYY-MM'),
    sa.Column('expiry_date', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True, comment='过期时间'),
    sa.Column('is_outdated', sa.BOOLEAN(), autoincrement=False, nullable=True, comment='是否已过时'),
    sa.Column('abstract', sa.TEXT(), autoincrement=False, nullable=True, comment='文档摘要'),
    sa.Column('table_of_contents', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='文档目录结构'),
    sa.Column('key_points', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='关键要点'),
    sa.Column('metadata_version', sa.INTEGER(), autoincrement=False, nullable=True, comment='元数据版本'),
    sa.Column('last_enriched_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True, comment='最后丰富时间'),
    sa.Column('enrichment_status', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='各字段填充状态'),
    sa.Column('reviewed_by', sa.VARCHAR(), autoincrement=False, nullable=True, comment='审核人'),
    sa.Column('reviewed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True, comment='审核时间'),
    sa.Column('review_notes', sa.TEXT(), autoincrement=False, nullable=True, comment='审核备注'),
    sa.Column('metadata_info', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('deleted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('document_metadata_document_id_fkey')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('document_metadata_project_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('document_metadata_pkey')),
    sa.UniqueConstraint('document_id', name=op.f('document_metadata_document_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_document_metadata_project_id'), 'document_metadata', ['project_id'], unique=False)
    op.create_table('document_references',
    sa.Column('citing_document_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('cited_document_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('reference_type', sa.VARCHAR(), autoincrement=False, nullable=True, comment='引用类型'),
    sa.Column('reference_context', sa.TEXT(), autoincrement=False, nullable=True, comment='引用上下文'),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['cited_document_id'], ['documents.id'], name=op.f('document_references_cited_document_id_fkey')),
    sa.ForeignKeyConstraint(['citing_document_id'], ['documents.id'], name=op.f('document_references_citing_document_id_fkey')),
    sa.PrimaryKeyConstraint('citing_document_id', 'cited_document_id', name=op.f('document_references_pkey'))
    )
    op.create_table('project_memories',
    sa.Column('project_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('context_summary', sa.TEXT(), autoincrement=False, nullable=True, comment='项目上下文摘要'),
    sa.Column('key_concepts', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='关键概念列表'),
    sa.Column('research_goals', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='研究目标'),
    sa.Column('learned_facts', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='学习到的事实'),
    sa.Column('important_documents', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='重要文档列表'),
    sa.Column('frequent_queries', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='常见查询'),
    sa.Column('completed_tasks', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='已完成任务'),
    sa.Column('pending_tasks', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='待处理任务'),
    sa.Column('milestones', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='里程碑'),
    sa.Column('total_documents', sa.INTEGER(), autoincrement=False, nullable=True, comment='文档总数'),
    sa.Column('total_queries', sa.INTEGER(), autoincrement=False, nullable=True, comment='查询总数'),
    sa.Column('avg_confidence', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True, comment='平均置信度'),
    sa.Column('last_activity_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True, comment='最后活动时间'),
    sa.Column('memory_version', sa.INTEGER(), autoincrement=False, nullable=True, comment='记忆版本'),
    sa.Column('metadata_info', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('deleted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('project_memories_project_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('project_memories_pkey'))
    )
    op.create_index(op.f('ix_project_memories_project_id'), 'project_memories', ['project_id'], unique=False)
    # ### end Alembic commands ###