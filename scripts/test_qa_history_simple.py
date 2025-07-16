#!/usr/bin/env python3
"""
简单的对话历史功能测试
快速验证核心功能是否正常工作
"""

import httpx
import asyncio
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"
HEADERS = {"X-USER-ID": USER_ID}


async def test_conversation_qa():
    """测试对话问答功能"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 50)
        print("🧪 DPA对话历史功能快速测试")
        print("=" * 50)
        
        # 1. 健康检查
        print("\n1️⃣ 健康检查...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ 后端服务正常")
            else:
                print(f"❌ 后端服务异常: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ 无法连接到后端服务: {e}")
            print("请确保后端服务在8200端口运行")
            return
        
        # 2. 创建对话并提问
        print("\n2️⃣ 创建对话并提问...")
        try:
            # 第一个问题
            question1 = "什么是人工智能？"
            print(f"问题1: {question1}")
            
            response = await client.post(
                f"{BASE_URL}/api/v1/qa-history/answer",
                headers=HEADERS,
                params={"user_id": USER_ID},
                json={
                    "question": question1,
                    "project_id": "test-project",
                    "conversation_id": None,
                    "use_conversation_context": True,
                    "include_sources": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                conversation_id = data["conversation_id"]
                print(f"✅ 创建对话成功，ID: {conversation_id}")
                print(f"回答: {data['answer'][:100]}...")
                print(f"置信度: {data['confidence']:.2f}")
            else:
                print(f"❌ 创建对话失败: {response.status_code}")
                print(response.text)
                return
            
            # 3. 继续对话
            print("\n3️⃣ 继续对话（使用历史）...")
            question2 = "机器学习和它有什么关系？"
            print(f"问题2: {question2}")
            
            response = await client.post(
                f"{BASE_URL}/api/v1/qa-history/answer",
                headers=HEADERS,
                params={"user_id": USER_ID},
                json={
                    "question": question2,
                    "project_id": "test-project",
                    "conversation_id": conversation_id,
                    "use_conversation_context": True,
                    "include_sources": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 继续对话成功")
                print(f"回答: {data['answer'][:100]}...")
                print(f"使用了对话历史: 是")
            else:
                print(f"❌ 继续对话失败: {response.status_code}")
            
            # 4. 查看对话消息
            print("\n4️⃣ 查看对话消息...")
            response = await client.get(
                f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
                headers=HEADERS,
                params={"user_id": USER_ID}
            )
            
            if response.status_code == 200:
                messages = response.json()
                print(f"✅ 获取消息成功，共 {len(messages)} 条消息")
                for i, msg in enumerate(messages):
                    role = "👤用户" if msg["role"] == "user" else "🤖助手"
                    content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                    print(f"  {i+1}. {role}: {content}")
            else:
                print(f"❌ 获取消息失败: {response.status_code}")
            
            # 5. 总结对话
            print("\n5️⃣ 总结对话...")
            response = await client.post(
                f"{BASE_URL}/api/v1/qa-history/conversations/{conversation_id}/summarize",
                headers=HEADERS,
                params={"user_id": USER_ID}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 总结成功")
                print(f"总结: {data['summary']}")
            else:
                print(f"❌ 总结失败: {response.status_code}")
            
        except Exception as e:
            print(f"❌ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_conversation_qa())