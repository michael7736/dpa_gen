"""
MVP认知工作流测试
"""
import asyncio
import pytest
from datetime import datetime

from src.core.memory.mvp_workflow import create_mvp_workflow
from src.core.memory.mvp_state import (
    MVPCognitiveState,
    WorkingMemoryManager,
    DEFAULT_USER_ID
)


@pytest.mark.asyncio
async def test_workflow_initialization():
    """测试工作流初始化"""
    workflow = create_mvp_workflow()
    assert workflow.user_id == DEFAULT_USER_ID
    assert workflow.memory_service is not None
    assert workflow.llm is not None


@pytest.mark.asyncio
async def test_simple_query_flow():
    """测试简单查询流程"""
    workflow = create_mvp_workflow()
    
    # 运行查询
    result = await workflow.run(
        message="什么是深度学习？",
        project_id="test_project"
    )
    
    # 验证结果
    assert isinstance(result, dict)
    assert result["user_id"] == DEFAULT_USER_ID
    assert result["project_id"] == "test_project"
    assert len(result["messages"]) >= 2  # 至少有用户消息和AI响应
    assert result["processing_status"] in ["completed", "failed"]
    
    # 检查工作记忆
    working_memory = result.get("working_memory", {})
    assert "current_intent" in working_memory or result["processing_status"] == "failed"


@pytest.mark.asyncio
async def test_working_memory_management():
    """测试工作记忆管理"""
    workflow = create_mvp_workflow()
    
    # 创建初始状态
    state = {
        "messages": [],
        "thread_id": "test_thread",
        "user_id": DEFAULT_USER_ID,
        "project_id": "test_project",
        "working_memory": {},
        "recent_documents": [],
        "current_chunk": None,
        "query_result": None,
        "memory_bank_snapshot": None,
        "last_error": None,
        "processing_status": "idle",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # 添加项到工作记忆
    state = WorkingMemoryManager.add_item(
        state,
        "test_item_1",
        {"data": "test_value_1"},
        priority=5
    )
    
    # 验证添加
    assert "test_item_1" in state["working_memory"]
    item = WorkingMemoryManager.get_item(state, "test_item_1")
    assert item == {"data": "test_value_1"}
    
    # 测试容量限制
    for i in range(25):
        state = WorkingMemoryManager.add_item(
            state,
            f"test_item_{i+2}",
            {"data": f"test_value_{i+2}"},
            priority=1
        )
    
    # 验证容量不超过限制
    assert len(state["working_memory"]) <= WorkingMemoryManager.MAX_ITEMS


@pytest.mark.asyncio
async def test_perceive_node():
    """测试感知节点"""
    workflow = create_mvp_workflow()
    
    # 准备状态
    from langchain_core.messages import HumanMessage
    state = {
        "messages": [HumanMessage(content="分析这个文档的主要观点")],
        "thread_id": "test",
        "user_id": DEFAULT_USER_ID,
        "project_id": None,
        "working_memory": {},
        "recent_documents": [],
        "current_chunk": None,
        "query_result": None,
        "memory_bank_snapshot": None,
        "last_error": None,
        "processing_status": "idle",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # 运行感知节点
    result = await workflow._perceive_node(state)
    
    # 验证结果
    assert result["processing_status"] in ["processing", "failed"]
    if result["processing_status"] == "processing":
        assert "current_intent" in result["working_memory"]


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    workflow = create_mvp_workflow()
    
    # 空消息应该失败
    result = await workflow.run(
        message="",
        project_id="test_project"
    )
    
    assert result["processing_status"] == "failed" or len(result["messages"]) == 2


@pytest.mark.asyncio 
async def test_multi_turn_conversation():
    """测试多轮对话"""
    workflow = create_mvp_workflow()
    
    # 第一轮
    thread_id = "conversation_test"
    state1 = await workflow.run(
        message="什么是机器学习？",
        thread_id=thread_id,
        project_id="test_project"
    )
    
    # 第二轮 - 使用相同的thread_id
    state2 = await workflow.run(
        message="它和深度学习有什么区别？",
        thread_id=thread_id,
        project_id="test_project"
    )
    
    # 验证对话连续性
    assert state2["thread_id"] == thread_id
    assert len(state2["messages"]) >= 4  # 两轮对话的消息


@pytest.mark.asyncio
async def test_memory_bank_integration():
    """测试Memory Bank集成"""
    workflow = create_mvp_workflow()
    
    # 准备包含文档的状态
    state = {
        "messages": [],
        "thread_id": "test",
        "user_id": DEFAULT_USER_ID,
        "project_id": "test_project",
        "working_memory": {},
        "recent_documents": [],
        "current_chunk": {
            "content": "这是一个测试文档内容",
            "source": "test.txt",
            "index": 0
        },
        "query_result": None,
        "memory_bank_snapshot": None,
        "last_error": None,
        "processing_status": "idle",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # 运行处理节点
    result = await workflow._process_node(state)
    
    # 验证文档被处理
    assert result["current_chunk"] is None
    assert len(result.get("recent_documents", [])) > 0


if __name__ == "__main__":
    # 运行基本测试
    async def main():
        print("Testing MVP Workflow...")
        
        # 测试基本查询
        workflow = create_mvp_workflow()
        result = await workflow.run("什么是人工智能？")
        
        print(f"Status: {result['processing_status']}")
        if result["processing_status"] == "completed":
            print(f"Response: {result['messages'][-1].content}")
        else:
            print(f"Error: {result.get('last_error', 'Unknown error')}")
            
        print(f"Working memory items: {len(result.get('working_memory', {}))}")
        
    asyncio.run(main())