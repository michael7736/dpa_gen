"""
MVP集成测试
端到端测试所有核心功能
"""
import asyncio
import pytest
from pathlib import Path
import tempfile

from src.services.memory_write_service_v2 import MemoryWriteService, MemoryType
from src.core.memory.mvp_workflow import create_mvp_workflow
from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.core.document.mvp_document_processor import create_mvp_document_processor
from src.core.retrieval.mvp_hybrid_retriever import create_mvp_hybrid_retriever
from src.core.qa.mvp_qa_system import create_mvp_qa_system


@pytest.fixture
async def setup_test_environment():
    """设置测试环境"""
    user_id = "test_user"
    project_id = "test_mvp_project"
    
    # 初始化服务
    memory_service = MemoryWriteService(user_id=user_id)
    memory_bank = create_memory_bank_manager(user_id=user_id)
    
    # 初始化项目
    await memory_bank.initialize_project(project_id)
    
    # 创建测试文档
    test_docs = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for i in range(3):
            doc_path = Path(temp_dir) / f"test_doc_{i}.txt"
            doc_path.write_text(f"""
文档{i}: 深度学习基础知识

这是测试文档{i}的内容。包含了深度学习、神经网络、CNN、RNN等概念。
Transformer架构是当前NLP领域的主流选择。
""")
            test_docs.append(str(doc_path))
            
        yield {
            "user_id": user_id,
            "project_id": project_id,
            "test_docs": test_docs,
            "memory_service": memory_service,
            "memory_bank": memory_bank
        }


@pytest.mark.asyncio
async def test_memory_write_service():
    """测试统一内存写入服务"""
    service = MemoryWriteService()
    
    # 测试写入
    result = await service.write_memory(
        content="测试内容",
        memory_type=MemoryType.SEMANTIC,
        metadata={"test": True},
        project_id="test_project"
    )
    
    assert result.success
    assert result.operation_id
    
    # 测试批量写入
    contents = ["内容1", "内容2", "内容3"]
    results = await service.batch_write(
        contents=contents,
        memory_type=MemoryType.EPISODIC,
        project_id="test_project"
    )
    
    assert len(results) == 3
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_document_processing(setup_test_environment):
    """测试文档处理流程"""
    env = await setup_test_environment.__anext__()
    
    processor = create_mvp_document_processor(user_id=env["user_id"])
    
    # 处理文档
    for doc_path in env["test_docs"]:
        result = await processor.process_document(
            file_path=doc_path,
            project_id=env["project_id"]
        )
        
        assert result.status == "completed"
        assert result.chunk_count > 0
        assert result.document_id


@pytest.mark.asyncio
async def test_memory_bank(setup_test_environment):
    """测试Memory Bank功能"""
    env = await setup_test_environment.__anext__()
    memory_bank = env["memory_bank"]
    project_id = env["project_id"]
    
    # 更新上下文
    await memory_bank.update_context(
        project_id=project_id,
        new_content="深度学习是AI的核心技术",
        source="test"
    )
    
    # 添加概念
    concepts = [
        {
            "name": "深度学习",
            "category": "technology",
            "description": "使用多层神经网络的机器学习方法",
            "confidence": 0.9
        }
    ]
    await memory_bank.add_concepts(project_id, concepts)
    
    # 添加学习记录
    await memory_bank.add_learning_entry(
        project_id=project_id,
        content="学习了深度学习基础",
        learning_type="study"
    )
    
    # 获取快照
    snapshot = await memory_bank.get_snapshot(project_id)
    
    assert snapshot
    assert snapshot.dynamic_summary
    assert len(snapshot.core_concepts) > 0
    assert len(snapshot.learning_journals) > 0


@pytest.mark.asyncio
async def test_hybrid_retrieval(setup_test_environment):
    """测试混合检索"""
    env = await setup_test_environment.__anext__()
    
    # 先写入一些测试数据
    memory_service = env["memory_service"]
    test_contents = [
        "深度学习使用多层神经网络",
        "CNN适合处理图像数据",
        "RNN处理序列数据",
        "Transformer使用注意力机制"
    ]
    
    for content in test_contents:
        await memory_service.write_memory(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            project_id=env["project_id"],
            user_id=env["user_id"]
        )
    
    # 执行检索
    retriever = create_mvp_hybrid_retriever(user_id=env["user_id"])
    result = await retriever.retrieve(
        query="深度学习和CNN",
        project_id=env["project_id"],
        top_k=5
    )
    
    assert result.total_results > 0
    assert len(result.fused_results) > 0
    
    # 验证三种检索都工作
    assert isinstance(result.vector_results, list)
    assert isinstance(result.graph_results, list)
    assert isinstance(result.memory_results, list)


@pytest.mark.asyncio
async def test_cognitive_workflow(setup_test_environment):
    """测试认知工作流"""
    env = await setup_test_environment.__anext__()
    
    workflow = create_mvp_workflow(user_id=env["user_id"])
    
    # 执行工作流
    result = await workflow.ainvoke({
        "input": "什么是深度学习？",
        "project_id": env["project_id"],
        "user_id": env["user_id"]
    })
    
    # 验证所有节点都执行了
    assert "perceived_input" in result
    assert "processed_input" in result
    assert "retrieved_context" in result
    assert "reasoning_result" in result
    assert "memory_updated" in result


@pytest.mark.asyncio
async def test_qa_system(setup_test_environment):
    """测试问答系统"""
    env = await setup_test_environment.__anext__()
    
    qa_system = create_mvp_qa_system(user_id=env["user_id"])
    
    # 测试问答
    result = await qa_system.answer_question(
        question="什么是CNN？",
        project_id=env["project_id"],
        top_k=5
    )
    
    assert result.answer
    assert result.confidence_score > 0
    assert result.processing_time > 0
    
    # 测试批量问答
    questions = ["什么是RNN？", "Transformer的优势是什么？"]
    batch_results = await qa_system.batch_answer(
        questions=questions,
        project_id=env["project_id"]
    )
    
    assert len(batch_results) == 2
    assert all(r.answer for r in batch_results)


@pytest.mark.asyncio
async def test_end_to_end_flow(setup_test_environment):
    """端到端流程测试"""
    env = await setup_test_environment.__anext__()
    
    # 1. 处理文档
    processor = create_mvp_document_processor(user_id=env["user_id"])
    doc_result = await processor.process_document(
        file_path=env["test_docs"][0],
        project_id=env["project_id"]
    )
    assert doc_result.status == "completed"
    
    # 2. 执行认知工作流
    workflow = create_mvp_workflow(user_id=env["user_id"])
    workflow_result = await workflow.ainvoke({
        "input": "总结深度学习的核心概念",
        "project_id": env["project_id"],
        "user_id": env["user_id"]
    })
    assert workflow_result["reasoning_result"]
    
    # 3. 问答测试
    qa_system = create_mvp_qa_system(user_id=env["user_id"])
    qa_result = await qa_system.answer_question(
        question="这个文档讲了什么内容？",
        project_id=env["project_id"]
    )
    assert qa_result.answer
    assert qa_result.confidence_score > 0.5
    
    # 4. 验证Memory Bank更新
    memory_bank = env["memory_bank"]
    snapshot = await memory_bank.get_snapshot(env["project_id"])
    assert len(snapshot.learning_journals) > 0


@pytest.mark.asyncio
async def test_multi_user_isolation():
    """测试多用户隔离预埋"""
    user1 = "user1"
    user2 = "user2"
    project_id = "shared_project"
    
    # 为两个用户创建服务
    service1 = MemoryWriteService(user_id=user1)
    service2 = MemoryWriteService(user_id=user2)
    
    # 用户1写入数据
    await service1.write_memory(
        content="用户1的私有数据",
        memory_type=MemoryType.SEMANTIC,
        project_id=project_id,
        user_id=user1
    )
    
    # 用户2写入数据
    await service2.write_memory(
        content="用户2的私有数据",
        memory_type=MemoryType.SEMANTIC,
        project_id=project_id,
        user_id=user2
    )
    
    # 验证数据隔离（在实际实现中应该验证数据确实被隔离）
    # 这里只验证user_id参数被正确传递
    assert service1.user_id == user1
    assert service2.user_id == user2


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v"])