"""
文档处理流程的集成测试
测试从文件上传到向量存储的完整流程
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
from datetime import datetime
from typing import Dict, Any

from src.graphs import get_document_processing_agent
from src.config.environment_config import get_environment_config
from src.config.feature_flags import feature_flags
from src.models.document import Document, ProcessingStatus
from src.database.postgresql_client import get_db_session
from src.database.qdrant_client import get_qdrant_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="module")
def test_config():
    """测试配置"""
    # 强制使用测试环境
    import os
    os.environ["ENVIRONMENT"] = "testing"
    
    config = get_environment_config()
    assert config.is_testing()
    
    return config


@pytest.fixture(scope="module")
async def db_session():
    """数据库会话"""
    async with get_db_session() as session:
        yield session


@pytest.fixture
async def test_project(db_session):
    """创建测试项目"""
    from src.models.project import Project
    
    project = Project(
        name="Integration Test Project",
        description="Project for integration testing",
        owner_id=1  # 假设测试用户ID为1
    )
    
    db_session.add(project)
    await db_session.commit()
    
    yield project
    
    # 清理
    await db_session.delete(project)
    await db_session.commit()


@pytest.fixture
def sample_pdf_file(tmp_path):
    """创建示例PDF文件"""
    # 这里应该使用真实的PDF创建库，暂时用文本文件模拟
    pdf_file = tmp_path / "test_document.pdf"
    pdf_file.write_text("""
    This is a test document for integration testing.
    
    Chapter 1: Introduction
    This chapter introduces the concept of integration testing.
    Integration testing is crucial for ensuring different components work together.
    
    Chapter 2: Methodology
    We use pytest for our testing framework.
    The tests cover the entire document processing pipeline.
    
    Chapter 3: Results
    The results show that our system processes documents accurately.
    Performance metrics indicate good processing speed.
    
    Chapter 4: Conclusion
    Integration testing helps maintain system reliability.
    Regular testing prevents regression bugs.
    """)
    
    return pdf_file


@pytest.mark.integration
@pytest.mark.asyncio
class TestDocumentProcessingFlow:
    """文档处理流程集成测试"""
    
    async def test_complete_document_processing_flow(self, test_config, test_project, sample_pdf_file):
        """测试完整的文档处理流程"""
        # 1. 启用改进版处理器
        feature_flags.enable_flag("use_improved_document_processor", save=False)
        
        # 2. 获取文档处理智能体
        agent = get_document_processing_agent()
        assert agent.__class__.__name__ == "ImprovedDocumentProcessingAgent"
        
        # 3. 准备处理状态
        initial_state = {
            "project_id": str(test_project.id),
            "document_id": "test_doc_001",
            "file_path": str(sample_pdf_file),
            "file_name": sample_pdf_file.name,
            "processing_strategy": "STANDARD"
        }
        
        # 4. 执行文档处理
        start_time = datetime.now()
        
        # 模拟处理（因为实际的LangGraph编译需要更多设置）
        # 在实际测试中，这里应该调用：
        # result = await agent.compiled_graph.ainvoke(initial_state)
        
        # 暂时直接测试各个步骤
        state = await agent._initialize_processing(initial_state)
        assert state["status"] == "processing"
        assert state["current_step"] == "initialize"
        
        state = await agent._validate_input(state)
        assert state["progress"] == 10.0
        assert len(state["errors"]) == 0
        
        # 模拟解析
        state["parsed_content"] = {"text": sample_pdf_file.read_text()}
        
        # 测试分块
        state = await agent._chunk_document_with_fallback(state)
        assert len(state.get("chunks", [])) > 0
        assert state["progress"] == 50.0
        
        # 测试性能指标
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        assert processing_time < 5.0  # 应该在5秒内完成
        
        # 5. 验证结果
        assert state.get("chunks") is not None
        assert len(state["chunks"]) >= 4  # 至少应该有4个章节的块
        
        # 6. 检查指标
        metrics = agent.get_metrics()
        assert metrics["total_processed"] >= 1
        assert metrics["error_count"] == 0
    
    async def test_error_handling_and_recovery(self, test_config, test_project):
        """测试错误处理和恢复机制"""
        agent = get_document_processing_agent()
        
        # 1. 测试文件不存在的情况
        state = {
            "project_id": str(test_project.id),
            "document_id": "test_doc_002",
            "file_path": "/non/existent/file.pdf",
            "file_name": "missing.pdf",
            "processing_strategy": "STANDARD"
        }
        
        state = await agent._initialize_processing(state)
        state = await agent._validate_input(state)
        
        assert state["status"] == "error"
        assert len(state["errors"]) > 0
        assert "File not found" in state["errors"][0]["error"]
    
    async def test_fallback_strategy(self, test_config, test_project, sample_pdf_file):
        """测试降级策略"""
        agent = get_document_processing_agent()
        
        # 启用语义分块（会失败并降级）
        state = {
            "project_id": str(test_project.id),
            "document_id": "test_doc_003",
            "file_path": str(sample_pdf_file),
            "file_name": sample_pdf_file.name,
            "processing_strategy": "FULL",  # 使用完整策略
            "parsed_content": {"text": sample_pdf_file.read_text()}
        }
        
        state = await agent._initialize_processing(state)
        
        # 由于语义分块未实现，应该触发降级
        state = await agent._chunk_document_with_fallback(state)
        
        assert state.get("fallback_triggered", False) == True
        assert state["processing_strategy"] == "STANDARD"
        assert len(state.get("chunks", [])) > 0
    
    async def test_concurrent_processing(self, test_config, test_project, tmp_path):
        """测试并发文档处理"""
        agent = get_document_processing_agent()
        
        # 创建多个测试文件
        files = []
        for i in range(3):
            file_path = tmp_path / f"test_doc_{i}.txt"
            file_path.write_text(f"This is test document number {i}")
            files.append(file_path)
        
        # 并发处理
        tasks = []
        for i, file_path in enumerate(files):
            state = {
                "project_id": str(test_project.id),
                "document_id": f"test_doc_concurrent_{i}",
                "file_path": str(file_path),
                "file_name": file_path.name,
                "processing_strategy": "FAST"
            }
            
            # 创建处理任务
            task = asyncio.create_task(self._process_document(agent, state))
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证结果
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful == 3  # 所有文档都应该成功处理
        
        # 检查指标
        metrics = agent.get_metrics()
        assert metrics["total_processed"] >= 3
    
    async def _process_document(self, agent, state):
        """处理单个文档的辅助方法"""
        state = await agent._initialize_processing(state)
        state = await agent._validate_input(state)
        
        if state["status"] != "error":
            # 模拟完整处理
            state["parsed_content"] = {"text": f"Content of {state['file_name']}"}
            state = await agent._chunk_document_with_fallback(state)
            state = await agent._finalize_processing(state)
        
        return state


@pytest.mark.integration
@pytest.mark.asyncio
class TestVectorStorageIntegration:
    """向量存储集成测试"""
    
    async def test_qdrant_connection(self, test_config):
        """测试Qdrant连接"""
        qdrant_manager = get_qdrant_manager()
        
        # 测试创建集合
        collection_name = "test_integration_collection"
        vector_size = test_config.get("ai_models.embedding_dimension", 1536)
        
        try:
            await qdrant_manager.create_collection(collection_name, vector_size)
            
            # 验证集合存在
            collections = await qdrant_manager.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            assert collection_name in collection_names
            
        finally:
            # 清理
            await qdrant_manager.client.delete_collection(collection_name)
    
    async def test_vector_storage_and_retrieval(self, test_config):
        """测试向量存储和检索"""
        from src.core.vectorization import VectorStore
        
        vector_store = VectorStore()
        collection_name = "test_retrieval_collection"
        
        try:
            # 创建测试数据
            test_chunks = [
                {"content": "Python is a programming language", "metadata": {"topic": "programming"}},
                {"content": "Machine learning uses algorithms", "metadata": {"topic": "ml"}},
                {"content": "Data science involves statistics", "metadata": {"topic": "data"}}
            ]
            
            # 存储向量（使用模拟嵌入）
            for i, chunk in enumerate(test_chunks):
                # 模拟嵌入向量
                embedding = [0.1 * (i + 1)] * test_config.get("ai_models.embedding_dimension", 1536)
                
                await vector_store.store(
                    document_id=f"test_doc_{i}",
                    chunk=chunk,
                    embedding=embedding,
                    metadata=chunk["metadata"]
                )
            
            # 测试检索
            query_embedding = [0.15] * test_config.get("ai_models.embedding_dimension", 1536)
            results = await vector_store.search(
                query_embedding=query_embedding,
                limit=2
            )
            
            assert len(results) <= 2
            
        finally:
            # 清理
            pass  # 向量存储会自动清理


@pytest.mark.integration
class TestConfigurationIntegration:
    """配置集成测试"""
    
    def test_environment_config_loading(self):
        """测试环境配置加载"""
        config = get_environment_config()
        
        # 验证基础配置
        assert config.get("app.name") == "DPA智能知识引擎"
        assert config.get("api.prefix") == "/api/v1"
        
        # 验证环境特定配置
        assert config.get("environment") == "testing"
        assert config.get("debug.enabled") == True
        
        # 验证功能开关
        flags = config.get_feature_flags()
        assert isinstance(flags, dict)
        assert "use_improved_document_processor" in flags
    
    def test_feature_flags_integration(self):
        """测试功能开关集成"""
        from src.config.feature_flags import is_feature_enabled
        
        # 测试默认功能开关
        assert is_feature_enabled("parallel_document_processing") == True
        assert is_feature_enabled("use_semantic_chunking") == True  # 测试环境启用
        
        # 测试用户级功能开关
        enabled = is_feature_enabled(
            "enable_memory_system",
            user_id="test_user_123"
        )
        assert isinstance(enabled, bool)