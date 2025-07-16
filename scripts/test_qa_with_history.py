#!/usr/bin/env python3
"""
测试带对话历史的问答系统
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"  # 默认用户ID


async def test_qa_with_history():
    """测试带对话历史的问答功能"""
    print("=" * 60)
    print("测试带对话历史的问答系统")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"X-USER-ID": USER_ID}
        
        # 1. 获取项目列表
        print("\n1. 获取项目列表...")
        response = await client.get(
            f"{BASE_URL}/api/v1/projects",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ 获取项目失败: {response.text}")
            return
        
        projects = response.json()["data"]
        if not projects:
            print("❌ 没有找到项目，请先创建项目并上传文档")
            return
        
        project = projects[0]
        project_id = project["id"]
        print(f"✅ 使用项目: {project['name']} (ID: {project_id})")
        
        # 2. 创建新对话并提问
        print("\n2. 创建新对话并提问...")
        question1 = "什么是深度学习？"
        
        response = await client.post(
            f"{BASE_URL}/api/v1/qa-history/answer",
            headers=headers,
            params={"user_id": USER_ID},
            json={
                "question": question1,
                "project_id": project_id,
                "conversation_id": None,  # 创建新对话
                "use_conversation_context": True,
                "max_history_messages": 10,
                "include_sources": True
            }
        )
        
        if response.status_code != 200:
            print(f"❌ 问答失败: {response.text}")
            return
        
        result1 = response.json()
        conversation_id = result1["conversation_id"]
        print(f"✅ 创建对话ID: {conversation_id}")
        print(f"✅ 问题: {question1}")
        print(f"✅ 回答: {result1['answer'][:200]}...")
        print(f"✅ 置信度: {result1['confidence']:.2f}")
        
        # 3. 在同一对话中继续提问
        print("\n3. 在同一对话中继续提问...")
        question2 = "能详细解释一下神经网络吗？"
        
        response = await client.post(
            f"{BASE_URL}/api/v1/qa-history/answer",
            headers=headers,
            params={"user_id": USER_ID},
            json={
                "question": question2,
                "project_id": project_id,
                "conversation_id": conversation_id,  # 使用现有对话
                "use_conversation_context": True,
                "max_history_messages": 10,
                "include_sources": True
            }
        )
        
        if response.status_code != 200:
            print(f"❌ 继续对话失败: {response.text}")
            return
        
        result2 = response.json()
        print(f"✅ 问题: {question2}")
        print(f"✅ 回答: {result2['answer'][:200]}...")
        print(f"✅ 使用了 {len(result2.get('context_used', []))} 条历史消息作为上下文")
        
        # 4. 获取对话继续建议
        print("\n4. 获取对话继续建议...")
        response = await client.get(
            f"{BASE_URL}/api/v1/qa-history/conversations/{conversation_id}/continue",
            headers=headers,
            params={"user_id": USER_ID}
        )
        
        if response.status_code == 200:
            continue_info = response.json()
            print(f"✅ 对话消息数: {len(continue_info['recent_messages'])}")
            print("✅ 建议的后续问题:")
            for q in continue_info.get('suggested_questions', []):
                print(f"   - {q}")
        
        # 5. 总结对话
        print("\n5. 总结对话内容...")
        response = await client.post(
            f"{BASE_URL}/api/v1/qa-history/conversations/{conversation_id}/summarize",
            headers=headers,
            params={"user_id": USER_ID}
        )
        
        if response.status_code == 200:
            summary_info = response.json()
            print(f"✅ 对话摘要: {summary_info['summary']}")
            if summary_info.get('updated_title'):
                print(f"✅ 更新的标题: {summary_info['updated_title']}")
        
        # 6. 查看对话历史
        print("\n6. 查看完整对话历史...")
        response = await client.get(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            headers=headers,
            params={"user_id": USER_ID}
        )
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ 对话包含 {len(messages)} 条消息:")
            for msg in messages:
                role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
                content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                print(f"   {role}: {content_preview}")
        
        # 7. 导出对话
        print("\n7. 导出对话...")
        response = await client.get(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/export",
            headers=headers,
            params={"user_id": USER_ID, "format": "markdown"}
        )
        
        if response.status_code == 200:
            export_data = response.json()
            print(f"✅ 导出成功: {export_data['filename']}")
            print(f"✅ 内容预览:\n{export_data['content'][:300]}...")
        
        print("\n" + "=" * 60)
        print("✅ 对话历史问答测试完成！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_qa_with_history())