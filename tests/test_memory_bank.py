"""
Memory Bank测试
"""
import asyncio
import pytest
from datetime import datetime
import json

from src.core.memory.memory_bank_manager import (
    create_memory_bank_manager,
    Concept,
    JournalEntry,
    MemoryBankMetadata
)


@pytest.mark.asyncio
async def test_initialize_project():
    """测试项目初始化"""
    manager = create_memory_bank_manager(user_id="u1")
    project_id = "test_project_init"
    
    # 初始化项目
    success = await manager.initialize_project(project_id)
    assert success is True
    
    # 验证文件创建
    project_path = manager._get_project_path(project_id)
    assert project_path.exists()
    assert (project_path / "metadata.json").exists()
    assert (project_path / "context.md").exists()
    assert (project_path / "summary.md").exists()
    assert (project_path / "concepts.json").exists()
    assert (project_path / "learning_journal").exists()


@pytest.mark.asyncio
async def test_update_context():
    """测试上下文更新"""
    manager = create_memory_bank_manager(user_id="u1")
    project_id = "test_context"
    
    # 初始化项目
    await manager.initialize_project(project_id)
    
    # 更新上下文
    test_content = "This is a test context update with important information."
    success = await manager.update_context(
        project_id=project_id,
        new_content=test_content,
        source="test"
    )
    assert success is True
    
    # 验证内容
    project_path = manager._get_project_path(project_id)
    context_content = await manager._read_file(project_path / "context.md")
    assert test_content in context_content
    
    # 测试大小限制
    large_content = "X" * (manager.MAX_CONTEXT_SIZE + 1000)
    success = await manager.update_context(
        project_id=project_id,
        new_content=large_content,
        source="large_test"
    )
    assert success is True
    
    # 验证内容被截断
    context_content = await manager._read_file(project_path / "context.md")
    assert len(context_content) <= manager.MAX_CONTEXT_SIZE


@pytest.mark.asyncio
async def test_add_concepts():
    """测试概念管理"""
    manager = create_memory_bank_manager(user_id="u1")
    project_id = "test_concepts"
    
    # 初始化项目
    await manager.initialize_project(project_id)
    
    # 添加概念
    test_concepts = [
        {
            "name": "深度学习",
            "category": "技术",
            "description": "基于神经网络的机器学习方法"
        },
        {
            "name": "神经网络",
            "category": "技术",
            "description": "模拟人脑的计算模型",
            "relationships": ["深度学习"]
        }
    ]
    
    added_count = await manager.add_concepts(project_id, test_concepts)
    assert added_count == 2
    
    # 验证概念存储
    concepts = await manager.search_concepts(project_id, "")
    assert len(concepts) >= 2
    
    # 测试更新现有概念
    added_count = await manager.add_concepts(project_id, test_concepts)
    assert added_count == 0  # 没有新概念
    
    # 验证频率更新
    concepts = await manager.search_concepts(project_id, "深度学习")
    assert len(concepts) > 0
    assert concepts[0]["frequency"] > 1


@pytest.mark.asyncio
async def test_search_concepts():
    """测试概念搜索"""
    manager = create_memory_bank_manager(user_id="u1")
    project_id = "test_search"
    
    # 初始化并添加概念
    await manager.initialize_project(project_id)
    
    test_concepts = [
        {"name": "机器学习", "category": "技术", "description": "让机器从数据中学习"},
        {"name": "深度学习", "category": "技术", "description": "机器学习的子领域"},
        {"name": "数据科学", "category": "领域", "description": "数据分析和机器学习的结合"}
    ]
    
    await manager.add_concepts(project_id, test_concepts)
    
    # 搜索测试
    results = await manager.search_concepts(project_id, "学习")
    assert len(results) >= 2
    
    # 类别过滤
    results = await manager.search_concepts(project_id, "", category="技术")
    assert len(results) == 2
    
    # 精确搜索
    results = await manager.search_concepts(project_id, "深度学习")
    assert len(results) == 1
    assert results[0]["name"] == "深度学习"


@pytest.mark.asyncio
async def test_update_summary():
    """测试摘要生成"""
    manager = create_memory_bank_manager(user_id="u1")
    project_id = "test_summary"
    
    # 初始化项目
    await manager.initialize_project(project_id)
    
    # 添加一些内容
    await manager.update_context(
        project_id,
        "项目专注于深度学习在自然语言处理中的应用研究。",
        "init"
    )
    
    await manager.add_concepts(project_id, [
        {"name": "深度学习", "category": "技术", "description": "AI核心技术"},
        {"name": "NLP", "category": "应用", "description": "自然语言处理"}
    ])
    
    # 生成摘要
    summary = await manager.update_summary(project_id, force_regenerate=True)
    assert len(summary) > 0
    assert "深度学习" in summary or "项目" in summary


@pytest.mark.asyncio
async def test_get_snapshot():
    """测试获取快照"""
    manager = create_memory_bank_manager(user_id="u1")
    project_id = "test_snapshot"
    
    # 初始化并添加数据
    await manager.initialize_project(project_id)
    await manager.update_context(project_id, "Test context", "test")
    await manager.add_concepts(project_id, [
        {"name": "Test Concept", "category": "test", "description": "Test"}
    ])
    
    # 获取快照
    snapshot = await manager.get_snapshot(project_id)
    
    assert snapshot["project_id"] == project_id
    assert snapshot["user_id"] == "u1"
    assert "context_preview" in snapshot
    assert snapshot["concepts_count"] == 1
    assert len(snapshot["top_concepts"]) > 0


@pytest.mark.asyncio
async def test_export_memory():
    """测试导出记忆"""
    manager = create_memory_bank_manager(user_id="u1")
    project_id = "test_export"
    
    # 初始化并添加数据
    await manager.initialize_project(project_id)
    await manager.update_context(project_id, "Export test context", "test")
    await manager.add_concepts(project_id, [
        {"name": "Export Test", "category": "test", "description": "Test export"}
    ])
    
    # 导出
    export_data = await manager.export_memory(project_id)
    
    assert export_data["project_id"] == project_id
    assert "context" in export_data
    assert "concepts" in export_data
    assert "learning_journal" in export_data
    assert export_data["statistics"]["total_concepts"] == 1


@pytest.mark.asyncio
async def test_multi_user_isolation():
    """测试多用户隔离"""
    # 用户1
    manager1 = create_memory_bank_manager(user_id="u1")
    project_id = "shared_project"
    
    await manager1.initialize_project(project_id)
    await manager1.update_context(project_id, "User 1 private data", "u1")
    
    # 用户2
    manager2 = create_memory_bank_manager(user_id="test_user")
    
    # 同名项目，但路径不同
    await manager2.initialize_project(project_id)
    await manager2.update_context(project_id, "User 2 private data", "test_user")
    
    # 验证隔离
    snapshot1 = await manager1.get_snapshot(project_id)
    snapshot2 = await manager2.get_snapshot(project_id)
    
    assert "User 1 private data" in snapshot1["context_preview"]
    assert "User 2 private data" in snapshot2["context_preview"]
    assert snapshot1["context_preview"] != snapshot2["context_preview"]


if __name__ == "__main__":
    # 运行基本测试
    async def main():
        print("Testing Memory Bank Manager...")
        
        # 测试初始化
        await test_initialize_project()
        print("✓ Project initialization test passed")
        
        # 测试上下文
        await test_update_context()
        print("✓ Context update test passed")
        
        # 测试概念
        await test_add_concepts()
        print("✓ Concept management test passed")
        
        # 测试搜索
        await test_search_concepts()
        print("✓ Concept search test passed")
        
        # 测试快照
        await test_get_snapshot()
        print("✓ Snapshot test passed")
        
        print("\nAll tests passed!")
        
    asyncio.run(main())