"""
改进版文档处理智能体的单元测试
"""

import pytest
import asyncio
import json
import hashlib
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.graphs.improved_document_processing_agent import (
    ImprovedDocumentProcessingAgent,
    DocumentProcessingState,
    ProcessingStrategy
)


class TestImprovedDocumentProcessingAgent:
    """测试改进版文档处理智能体"""
    
    @pytest.fixture
    def agent(self):
        """创建智能体实例"""
        # 创建一个带有progress_callback的智能体
        progress_callback = AsyncMock()
        return ImprovedDocumentProcessingAgent(progress_callback=progress_callback)
    
    @pytest.fixture
    def sample_state(self, tmp_path):
        """创建示例状态"""
        # 创建临时测试文件
        test_file = tmp_path / "test_document.pdf"
        test_file.write_text("This is a test document content.")
        
        return DocumentProcessingState(
            project_id="test_project_123",
            document_id="test_doc_456",
            file_path=str(test_file),
            file_name="test_document.pdf",
            processing_strategy=ProcessingStrategy.STANDARD,
            current_step="",
            progress=0.0,
            status="pending",
            errors=[],
            warnings=[],
            parsed_content=None,
            chunks=[],
            embeddings=[],
            indexed=False,
            processing_start_time=datetime.now(),
            processing_end_time=None,
            step_durations={},
            retry_count=0,
            max_retries=3,
            fallback_triggered=False,
            metadata={},
            quality_score=0.0,
            document_hash="",
            use_cache=True
        )
    
    @pytest.mark.asyncio
    async def test_initialize_processing(self, agent, sample_state):
        """测试初始化处理"""
        result = await agent._initialize_processing(sample_state)
        
        assert result["status"] == "processing"
        assert result["progress"] == 0.0
        assert result["current_step"] == "initialize"
        assert result["errors"] == []
        assert result["warnings"] == []
        assert result["max_retries"] == 3
    
    @pytest.mark.asyncio
    async def test_validate_input_success(self, agent, sample_state):
        """测试输入验证成功"""
        result = await agent._validate_input(sample_state)
        
        assert result["progress"] == 10.0
        assert result["current_step"] == "validate_input"
        assert len(result["errors"]) == 0
        assert "validate_input" in result["step_durations"]
    
    @pytest.mark.asyncio
    async def test_validate_input_file_not_found(self, agent, sample_state):
        """测试文件不存在的情况"""
        sample_state["file_path"] = "/non/existent/file.pdf"
        
        result = await agent._validate_input(sample_state)
        
        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert "File not found" in result["errors"][0]["error"]
    
    @pytest.mark.asyncio
    async def test_validate_input_unsupported_type(self, agent, sample_state, tmp_path):
        """测试不支持的文件类型"""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("test")
        sample_state["file_path"] = str(test_file)
        
        result = await agent._validate_input(sample_state)
        
        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert "Unsupported file type" in result["errors"][0]["error"]
    
    @pytest.mark.asyncio
    async def test_parse_document_with_retry(self, agent, sample_state):
        """测试文档解析重试机制"""
        # 模拟前两次失败，第三次成功
        with patch.object(agent, '_standard_parse') as mock_parse:
            mock_parse.side_effect = [
                Exception("Parse error 1"),
                Exception("Parse error 2"),
                {"text": "Parsed content"}
            ]
            
            # 第一次尝试
            result = await agent._parse_document_with_retry(sample_state)
            assert result["retry_count"] == 1
            assert len(result["errors"]) == 1
            
            # 第二次尝试
            result = await agent._parse_document_with_retry(result)
            assert result["retry_count"] == 2
            assert len(result["errors"]) == 2
            
            # 第三次尝试（成功）
            result = await agent._parse_document_with_retry(result)
            assert result["parsed_content"] == {"text": "Parsed content"}
            assert result["retry_count"] == 0  # 成功后重置
    
    @pytest.mark.asyncio
    async def test_chunk_document_with_fallback(self, agent, sample_state):
        """测试分块降级策略"""
        sample_state["parsed_content"] = {"text": "Test content for chunking"}
        sample_state["processing_strategy"] = ProcessingStrategy.FULL
        
        # 模拟语义分块失败，降级到标准分块
        with patch.object(agent, '_semantic_chunking') as mock_semantic:
            with patch.object(agent, '_standard_chunking') as mock_standard:
                mock_semantic.side_effect = Exception("Semantic chunking failed")
                mock_standard.return_value = [{"content": "chunk1"}, {"content": "chunk2"}]
                
                # 第一次尝试（语义分块失败）
                result = await agent._chunk_document_with_fallback(sample_state)
                assert result["fallback_triggered"] == True
                assert result["processing_strategy"] == ProcessingStrategy.STANDARD
                assert len(result["warnings"]) == 1
                
                # 第二次尝试（使用标准分块）
                result = await agent._chunk_document_with_fallback(result)
                assert result["chunks"] == [{"content": "chunk1"}, {"content": "chunk2"}]
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, agent, sample_state):
        """测试批量生成嵌入"""
        # 创建测试chunks
        sample_state["chunks"] = [
            {"content": f"chunk_{i}", "index": i}
            for i in range(25)  # 测试批处理
        ]
        
        # 模拟向量存储
        with patch.object(agent.vector_store, 'embed_batch') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3]] * 10  # 模拟嵌入向量
            
            result = await agent._generate_embeddings_batch(sample_state)
            
            assert len(result["embeddings"]) == 25
            assert result["progress"] <= 90.0
            # 验证批处理调用次数（25个chunks，每批10个，应该调用3次）
            assert mock_embed.call_count == 3
    
    @pytest.mark.asyncio
    async def test_store_results_validation(self, agent, sample_state):
        """测试结果存储验证"""
        # chunks和embeddings数量不匹配
        sample_state["chunks"] = [{"content": "chunk1"}, {"content": "chunk2"}]
        sample_state["embeddings"] = [[0.1, 0.2]]  # 只有一个嵌入
        
        result = await agent._store_results_with_validation(sample_state)
        
        assert result["status"] == "error"
        assert len(result["errors"]) == 1
        assert "count mismatch" in result["errors"][0]["error"]
    
    @pytest.mark.asyncio
    async def test_store_results_partial_success(self, agent, sample_state):
        """测试部分存储成功的情况"""
        sample_state["chunks"] = [{"content": "chunk1"}, {"content": "chunk2"}]
        sample_state["embeddings"] = [[0.1, 0.2], [0.3, 0.4]]
        
        # 模拟第二个chunk存储失败
        with patch.object(agent.vector_store, 'store') as mock_store:
            mock_store.side_effect = [None, Exception("Storage error")]
            
            result = await agent._store_results_with_validation(sample_state)
            
            assert result["indexed"] == True  # 至少有一个成功
            assert len(result["warnings"]) == 2  # 一个失败警告 + 一个汇总警告
            assert "1/2 chunks were stored successfully" in result["warnings"][1]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, agent, sample_state):
        """测试错误处理"""
        sample_state["errors"] = [
            {"step": "parse", "error": "Parse failed"},
            {"step": "chunk", "error": "Chunk failed"}
        ]
        
        with patch.object(agent, '_cleanup_resources') as mock_cleanup:
            result = await agent._handle_error(sample_state)
            
            assert result["status"] == "error"
            assert result["current_step"] == "error_handling"
            assert mock_cleanup.called
            assert agent.metrics["error_count"] == 1
    
    @pytest.mark.asyncio
    async def test_finalize_processing_success(self, agent, sample_state):
        """测试成功完成处理"""
        sample_state["status"] = "processing"
        sample_state["chunks"] = [{"content": "chunk1"}, {"content": "chunk2"}]
        
        result = await agent._finalize_processing(sample_state)
        
        assert result["status"] == "completed"
        assert result["progress"] == 100.0
        assert result["processing_end_time"] is not None
        assert agent.metrics["total_processed"] == 1
        assert agent.metrics["success_count"] == 1
    
    def test_check_parsing_result(self, agent):
        """测试解析结果检查"""
        # 成功情况
        state = {"parsed_content": {"text": "content"}}
        assert agent._check_parsing_result(state) == "success"
        
        # 需要重试
        state = {"parsed_content": None, "retry_count": 1, "max_retries": 3}
        assert agent._check_parsing_result(state) == "retry"
        
        # 错误情况
        state = {"parsed_content": None, "retry_count": 3, "max_retries": 3}
        assert agent._check_parsing_result(state) == "error"
    
    def test_check_chunking_result(self, agent):
        """测试分块结果检查"""
        # 成功情况
        state = {"chunks": [{"content": "chunk1"}]}
        assert agent._check_chunking_result(state) == "success"
        
        # 需要降级
        state = {"chunks": [], "fallback_triggered": True}
        assert agent._check_chunking_result(state) == "fallback"
        
        # 错误情况
        state = {"chunks": [], "fallback_triggered": False}
        assert agent._check_chunking_result(state) == "error"
    
    def test_get_metrics(self, agent):
        """测试获取性能指标"""
        agent.metrics = {
            "total_processed": 10,
            "success_count": 8,
            "error_count": 2,
            "fallback_count": 3,
            "cache_hits": 4
        }
        
        metrics = agent.get_metrics()
        
        assert metrics["success_rate"] == 0.8
        assert metrics["fallback_rate"] == 0.3
        assert metrics["cache_hit_rate"] == 0.4
        assert metrics["total_processed"] == 10
    
    @pytest.mark.asyncio
    async def test_check_cache_hit(self, agent, sample_state, tmp_path):
        """测试缓存命中"""
        # 计算文档哈希
        with open(sample_state["file_path"], 'rb') as f:
            content = f.read()
            sample_state["document_hash"] = hashlib.sha256(content).hexdigest()
        
        # 创建缓存文件
        cache_data = {
            "chunks": [{"content": "cached chunk"}],
            "embeddings": [[0.1, 0.2, 0.3]],
            "metadata": {"title": "Cached Document"},
            "quality_score": 0.85
        }
        
        cache_file = agent.cache_dir / f"{sample_state['document_hash']}.json"
        cache_file.write_text(json.dumps(cache_data))
        
        result = await agent._check_cache(sample_state)
        
        assert result["status"] == "cached"
        assert result["chunks"] == cache_data["chunks"]
        assert result["metadata"]["title"] == "Cached Document"
        assert result["quality_score"] == 0.85
        assert agent.metrics["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_check_cache_miss(self, agent, sample_state):
        """测试缓存未命中"""
        sample_state["document_hash"] = "non_existent_hash"
        
        result = await agent._check_cache(sample_state)
        
        assert result.get("status") != "cached"
        assert result.get("chunks") == []
    
    @pytest.mark.asyncio
    async def test_extract_metadata(self, agent, sample_state):
        """测试元数据提取"""
        sample_state["parsed_content"] = {
            "text": "Document content",
            "pages": 5,
            "metadata": {"author": "Test Author"}
        }
        
        result = await agent._extract_metadata(sample_state)
        
        assert result["metadata"]["file_name"] == "test_document.pdf"
        assert result["metadata"]["pages"] == 5
        assert result["metadata"]["author"] == "Test Author"
        assert result["progress"] == 35.0
        assert "extract_metadata" in result["step_durations"]
    
    @pytest.mark.asyncio
    async def test_assess_document_quality(self, agent, sample_state):
        """测试文档质量评估"""
        # 高质量文档
        sample_state["parsed_content"] = {
            "text": "# Title\n\nThis is a well-structured document.\n\n## Section 1\n\nContent with paragraphs." * 100
        }
        
        result = await agent._assess_document_quality(sample_state)
        
        assert result["quality_score"] > 0.5
        assert result["progress"] == 40.0
        assert "assess_quality" in result["step_durations"]
        
        # 低质量文档
        sample_state["parsed_content"] = {"text": "short text"}
        sample_state["processing_strategy"] = ProcessingStrategy.FULL
        
        result = await agent._assess_document_quality(sample_state)
        
        assert result["quality_score"] < 0.5
        assert "Low quality document detected" in result["warnings"]
        assert result["processing_strategy"] == ProcessingStrategy.STANDARD
    
    @pytest.mark.asyncio
    async def test_update_cache(self, agent, sample_state):
        """测试缓存更新"""
        sample_state["document_hash"] = "test_hash_123"
        sample_state["chunks"] = [{"content": "chunk1"}]
        sample_state["embeddings"] = [[0.1, 0.2]]
        sample_state["metadata"] = {"title": "Test Doc"}
        sample_state["quality_score"] = 0.75
        sample_state["status"] = "completed"
        
        result = await agent._update_cache(sample_state)
        
        # 验证缓存文件已创建
        cache_file = agent.cache_dir / "test_hash_123.json"
        assert cache_file.exists()
        
        # 验证缓存内容
        with open(cache_file) as f:
            cache_data = json.load(f)
            assert cache_data["chunks"] == sample_state["chunks"]
            assert cache_data["quality_score"] == 0.75
    
    @pytest.mark.asyncio
    async def test_semantic_chunking(self, agent):
        """测试语义分块"""
        content = "This is a test document. It has multiple sentences. Each sentence is important."
        
        with patch('langchain_experimental.text_splitter.SemanticChunker') as mock_chunker:
            mock_instance = MagicMock()
            mock_instance.split_text.return_value = [
                "This is a test document.",
                "It has multiple sentences. Each sentence is important."
            ]
            mock_chunker.return_value = mock_instance
            
            chunks = await agent._semantic_chunking(content)
            
            assert len(chunks) == 2
            assert chunks[0]["metadata"]["chunking_method"] == "semantic"
            assert mock_instance.split_text.called
    
    @pytest.mark.asyncio
    async def test_process_document_batch(self, agent):
        """测试批量文档处理"""
        documents = [
            {
                "project_id": "test_project",
                "document_id": f"doc_{i}",
                "file_path": f"/path/to/doc_{i}.pdf",
                "file_name": f"doc_{i}.pdf",
                "processing_strategy": ProcessingStrategy.FAST
            }
            for i in range(5)
        ]
        
        # Mock the compiled graph
        with patch.object(agent.compiled_graph, 'ainvoke') as mock_invoke:
            mock_invoke.return_value = {"status": "completed", "document_id": "doc_0"}
            
            results = await agent.process_document_batch(documents, max_concurrent=2)
            
            assert len(results) == 5
            assert mock_invoke.call_count == 5
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, agent, sample_state):
        """测试进度回调"""
        # 初始化时应该触发回调
        await agent._initialize_processing(sample_state)
        
        agent.progress_callback.assert_called_once()
        call_args = agent.progress_callback.call_args[0][0]
        assert call_args["document_id"] == sample_state["document_id"]
        assert call_args["step"] == "initialize"
        assert call_args["progress"] == 0.0


@pytest.mark.asyncio
async def test_full_workflow(tmp_path):
    """测试完整工作流"""
    # 创建测试文件
    test_file = tmp_path / "test_document.txt"
    test_file.write_text("This is a test document with some content for processing.")
    
    # 创建带进度回调的智能体
    progress_updates = []
    async def progress_callback(update):
        progress_updates.append(update)
    
    agent = ImprovedDocumentProcessingAgent(progress_callback=progress_callback)
    
    # 准备初始状态
    initial_state = {
        "project_id": "test_project",
        "document_id": "test_doc",
        "file_path": str(test_file),
        "file_name": "test_document.txt",
        "processing_strategy": ProcessingStrategy.STANDARD
    }
    
    # 模拟必要的依赖
    with patch.object(agent, '_standard_parse') as mock_parse:
        with patch.object(agent.vector_store, 'embed_batch') as mock_embed:
            with patch.object(agent.vector_store, 'store') as mock_store:
                mock_parse.return_value = {"text": test_file.read_text()}
                mock_embed.return_value = [[0.1, 0.2, 0.3]]
                mock_store.return_value = None
                
                # Mock the document loader
                with patch('langchain.document_loaders.TextLoader') as mock_loader:
                    mock_loader.return_value.load.return_value = [
                        MagicMock(page_content=test_file.read_text(), metadata={})
                    ]
                    
                    # 执行工作流的部分步骤来验证功能
                    state = await agent._initialize_processing(initial_state)
                    assert len(progress_updates) > 0
                    assert state["document_hash"] != ""
                    
                    state = await agent._validate_input(state)
                    assert state["progress"] == 10.0
                    
                    # 验证缓存功能
                    cache_result = await agent._check_cache(state)
                    assert cache_result.get("status") != "cached"  # 第一次运行，不应该有缓存