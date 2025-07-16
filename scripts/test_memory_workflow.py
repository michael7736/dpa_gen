#!/usr/bin/env python3
"""
测试记忆工作流的CLI工具
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
import json

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.memory.mvp_workflow import create_mvp_workflow
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def interactive_chat():
    """交互式聊天测试"""
    print("\n=== DPA Memory Workflow Interactive Test ===")
    print("Type 'exit' to quit, 'new' to start a new conversation\n")
    
    workflow = create_mvp_workflow(user_id="u1")
    thread_id = None
    project_id = "test_project"
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'exit':
                print("\nGoodbye!")
                break
            elif user_input.lower() == 'new':
                thread_id = None
                print("\n--- New conversation started ---")
                continue
            elif not user_input:
                continue
                
            # 运行工作流
            print("\nThinking...")
            result = await workflow.run(
                message=user_input,
                thread_id=thread_id,
                project_id=project_id
            )
            
            # 保存thread_id以继续对话
            thread_id = result["thread_id"]
            
            # 显示响应
            if result["processing_status"] == "completed":
                # 找到AI响应
                ai_response = None
                for msg in reversed(result["messages"]):
                    if hasattr(msg, 'type') and msg.type == "ai":
                        ai_response = msg.content
                        break
                        
                if ai_response:
                    print(f"\nAssistant: {ai_response}")
                else:
                    print("\nAssistant: [No response generated]")
                    
                # 显示记忆状态
                if result.get("memory_bank_snapshot"):
                    snapshot = result["memory_bank_snapshot"]
                    print(f"\n[Memory: {snapshot.get('concepts_count', 0)} concepts, "
                          f"{snapshot.get('interactions_count', 0)} interactions]")
            else:
                print(f"\nError: {result.get('last_error', 'Unknown error')}")
                
            # 显示工作记忆状态
            working_memory = result.get("working_memory", {})
            print(f"[Working memory: {len(working_memory)} items]")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"\nError: {e}")
            logger.error(f"Chat error: {e}", exc_info=True)


async def test_document_processing():
    """测试文档处理"""
    print("\n=== Testing Document Processing ===")
    
    workflow = create_mvp_workflow(user_id="u1")
    
    # 模拟文档块
    test_chunks = [
        "深度学习是机器学习的一个子领域，它基于人工神经网络的学习算法。",
        "卷积神经网络（CNN）在图像识别任务中表现出色。",
        "循环神经网络（RNN）适合处理序列数据，如文本和时间序列。"
    ]
    
    for i, chunk in enumerate(test_chunks):
        print(f"\nProcessing chunk {i+1}/{len(test_chunks)}...")
        
        # 创建带有文档块的状态
        from src.core.memory.mvp_state import create_initial_state
        state = create_initial_state(user_id="u1", project_id="test_docs")
        state["current_chunk"] = {
            "content": chunk,
            "source": "test_document.txt",
            "index": i
        }
        
        # 处理文档
        result = await workflow._process_node(state)
        
        if result.get("last_error"):
            print(f"Error: {result['last_error']}")
        else:
            print(f"✓ Chunk processed successfully")
            print(f"  Recent documents: {len(result.get('recent_documents', []))}")


async def test_memory_search():
    """测试记忆搜索"""
    print("\n=== Testing Memory Search ===")
    
    workflow = create_mvp_workflow(user_id="u1")
    
    # 先写入一些测试数据
    test_queries = [
        "深度学习的基本原理是什么？",
        "CNN和RNN的区别是什么？",
        "如何选择合适的神经网络架构？"
    ]
    
    print("\nWriting test memories...")
    for query in test_queries:
        result = await workflow.run(
            message=query,
            project_id="test_search"
        )
        if result["processing_status"] == "completed":
            print(f"✓ Processed: {query[:30]}...")
        else:
            print(f"✗ Failed: {query[:30]}...")
            
    # 测试搜索
    print("\nSearching memories...")
    search_query = "神经网络"
    
    from src.services.memory_write_service_v2 import MemoryWriteService
    service = MemoryWriteService(user_id="u1")
    
    try:
        results = await service.search_memories(
            query=search_query,
            project_id="test_search",
            limit=5
        )
        
        print(f"\nSearch results for '{search_query}':")
        for i, result in enumerate(results):
            print(f"{i+1}. {result.get('content', '')[:100]}...")
            
    except Exception as e:
        print(f"Search error: {e}")


async def test_multi_user_isolation():
    """测试多用户隔离"""
    print("\n=== Testing Multi-User Isolation ===")
    
    # 创建两个用户的工作流
    workflow_u1 = create_mvp_workflow(user_id="u1")
    workflow_u2 = create_mvp_workflow(user_id="test_user")
    
    # 用户1写入数据
    print("\nUser 'u1' writing data...")
    result1 = await workflow_u1.run(
        message="用户1的私密信息：我的密码是123456",
        project_id="private_u1"
    )
    
    # 用户2写入数据
    print("\nUser 'test_user' writing data...")
    result2 = await workflow_u2.run(
        message="用户2的私密信息：我的账号是test@example.com",
        project_id="private_u2"
    )
    
    # 验证隔离
    print("\nVerifying isolation...")
    print(f"User u1 thread: {result1['thread_id']}")
    print(f"User test_user thread: {result2['thread_id']}")
    
    # 检查Memory Bank路径
    from pathlib import Path
    from src.config.settings import settings
    
    mb_path = Path(settings.paths.memory_bank)
    u1_path = mb_path / "project_private_u1"
    u2_path = mb_path / "project_private_u2"
    
    print(f"\nMemory Bank paths:")
    print(f"User u1: {u1_path} (exists: {u1_path.exists()})")
    print(f"User test_user: {u2_path} (exists: {u2_path.exists()})")


async def main():
    """主函数"""
    print("\n=== DPA Memory Workflow Test Suite ===")
    print("\nSelect test mode:")
    print("1. Interactive chat")
    print("2. Document processing")
    print("3. Memory search")
    print("4. Multi-user isolation")
    print("5. Run all tests")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        await interactive_chat()
    elif choice == "2":
        await test_document_processing()
    elif choice == "3":
        await test_memory_search()
    elif choice == "4":
        await test_multi_user_isolation()
    elif choice == "5":
        await test_document_processing()
        await test_memory_search()
        await test_multi_user_isolation()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        logger.error("Test failed", exc_info=True)