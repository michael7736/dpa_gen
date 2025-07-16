#!/usr/bin/env python3
"""
DPA对话历史功能集成测试
测试完整的对话历史持久化功能流程
"""

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"
HEADERS = {"X-USER-ID": USER_ID}

# 测试结果
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)


def print_test(name: str, passed: bool, error: str = None):
    """打印测试结果"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ {name}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {error}")
        print(f"❌ {name}")
        if error:
            print(f"   错误: {error}")


async def test_health_check(client: httpx.AsyncClient):
    """测试健康检查"""
    print_header("健康检查")
    
    try:
        # 测试主健康检查
        response = await client.get(f"{BASE_URL}/health")
        print_test("主健康检查", response.status_code == 200)
        
        # 测试对话历史健康检查
        response = await client.get(f"{BASE_URL}/api/v1/qa-history/health")
        print_test("对话历史服务健康检查", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   服务状态: {data.get('status')}")
            print(f"   功能特性: {', '.join(data.get('features', []))}")
        
    except Exception as e:
        print_test("健康检查", False, str(e))


async def test_conversation_management(client: httpx.AsyncClient) -> Dict[str, str]:
    """测试对话管理功能"""
    print_header("对话管理功能")
    
    result = {}
    
    try:
        # 1. 创建对话
        create_data = {
            "title": "集成测试对话",
            "project_id": None,  # 可以为空
            "settings": {"test": True}
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/conversations",
            headers=HEADERS,
            params={"user_id": USER_ID},
            json=create_data
        )
        print_test("创建对话", response.status_code == 200)
        
        if response.status_code == 200:
            conversation = response.json()
            result["conversation_id"] = conversation["id"]
            print(f"   对话ID: {conversation['id']}")
            print(f"   标题: {conversation['title']}")
        
        # 2. 获取对话列表
        response = await client.get(
            f"{BASE_URL}/api/v1/conversations",
            headers=HEADERS,
            params={"user_id": USER_ID}
        )
        print_test("获取对话列表", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   对话数量: {data['total']}")
        
        # 3. 获取对话详情
        if "conversation_id" in result:
            response = await client.get(
                f"{BASE_URL}/api/v1/conversations/{result['conversation_id']}",
                headers=HEADERS,
                params={"user_id": USER_ID}
            )
            print_test("获取对话详情", response.status_code == 200)
        
    except Exception as e:
        print_test("对话管理", False, str(e))
    
    return result


async def test_qa_with_history(client: httpx.AsyncClient, project_id: str = None) -> Dict[str, Any]:
    """测试带历史的问答功能"""
    print_header("带历史的问答功能")
    
    result = {}
    
    try:
        # 1. 第一次提问（创建新对话）
        question1 = "什么是机器学习？"
        response = await client.post(
            f"{BASE_URL}/api/v1/qa-history/answer",
            headers=HEADERS,
            params={"user_id": USER_ID},
            json={
                "question": question1,
                "project_id": project_id or "test-project",
                "conversation_id": None,
                "use_conversation_context": True,
                "max_history_messages": 10,
                "include_sources": True
            }
        )
        print_test("第一次提问（创建新对话）", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            result["conversation_id"] = data["conversation_id"]
            result["first_answer"] = data["answer"]
            print(f"   对话ID: {data['conversation_id']}")
            print(f"   回答预览: {data['answer'][:100]}...")
            print(f"   置信度: {data['confidence']:.2f}")
        
        # 2. 第二次提问（使用对话历史）
        if "conversation_id" in result:
            question2 = "深度学习和机器学习有什么区别？"
            response = await client.post(
                f"{BASE_URL}/api/v1/qa-history/answer",
                headers=HEADERS,
                params={"user_id": USER_ID},
                json={
                    "question": question2,
                    "project_id": project_id or "test-project",
                    "conversation_id": result["conversation_id"],
                    "use_conversation_context": True,
                    "max_history_messages": 10,
                    "include_sources": True
                }
            )
            print_test("第二次提问（使用对话历史）", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   使用了历史上下文: {'是' if data.get('context_used') else '否'}")
                print(f"   回答预览: {data['answer'][:100]}...")
        
        # 3. 继续对话
        if "conversation_id" in result:
            response = await client.get(
                f"{BASE_URL}/api/v1/qa-history/conversations/{result['conversation_id']}/continue",
                headers=HEADERS,
                params={"user_id": USER_ID}
            )
            print_test("获取对话继续建议", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   最近消息数: {len(data['recent_messages'])}")
                print(f"   建议问题数: {len(data['suggested_questions'])}")
                if data['suggested_questions']:
                    print(f"   建议示例: {data['suggested_questions'][0]}")
        
        # 4. 总结对话
        if "conversation_id" in result:
            response = await client.post(
                f"{BASE_URL}/api/v1/qa-history/conversations/{result['conversation_id']}/summarize",
                headers=HEADERS,
                params={"user_id": USER_ID}
            )
            print_test("总结对话", response.status_code == 200)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   总结: {data['summary'][:100]}...")
        
    except Exception as e:
        print_test("带历史的问答", False, str(e))
    
    return result


async def test_conversation_export(client: httpx.AsyncClient, conversation_id: str):
    """测试对话导出功能"""
    print_header("对话导出功能")
    
    try:
        # 1. 导出为JSON
        response = await client.get(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/export",
            headers=HEADERS,
            params={"user_id": USER_ID, "format": "json"}
        )
        print_test("导出为JSON格式", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   格式: {data['format']}")
            print(f"   消息数: {len(data['data']['messages'])}")
        
        # 2. 导出为Markdown
        response = await client.get(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/export",
            headers=HEADERS,
            params={"user_id": USER_ID, "format": "markdown"}
        )
        print_test("导出为Markdown格式", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   文件名: {data['filename']}")
            print(f"   内容预览: {data['content'][:100]}...")
        
    except Exception as e:
        print_test("对话导出", False, str(e))


async def test_conversation_messages(client: httpx.AsyncClient, conversation_id: str):
    """测试对话消息管理"""
    print_header("对话消息管理")
    
    try:
        # 1. 获取消息列表
        response = await client.get(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            headers=HEADERS,
            params={"user_id": USER_ID}
        )
        print_test("获取消息列表", response.status_code == 200)
        
        if response.status_code == 200:
            messages = response.json()
            print(f"   消息数量: {len(messages)}")
            for i, msg in enumerate(messages[:3]):  # 显示前3条
                role = "用户" if msg["role"] == "user" else "助手"
                content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                print(f"   {i+1}. {role}: {content_preview}")
        
        # 2. 添加新消息
        response = await client.post(
            f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
            headers=HEADERS,
            params={"user_id": USER_ID},
            json={
                "role": "user",
                "content": "这是一条测试消息",
                "message_type": "text"
            }
        )
        print_test("添加新消息", response.status_code == 200)
        
    except Exception as e:
        print_test("消息管理", False, str(e))


async def test_project_integration(client: httpx.AsyncClient):
    """测试与项目系统的集成"""
    print_header("项目系统集成")
    
    try:
        # 1. 获取项目列表
        response = await client.get(
            f"{BASE_URL}/api/v1/projects",
            headers=HEADERS
        )
        print_test("获取项目列表", response.status_code == 200)
        
        project_id = None
        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                project_id = data["data"][0]["id"]
                print(f"   找到项目: {data['data'][0]['name']} (ID: {project_id})")
                
                # 2. 在项目中创建对话
                response = await client.post(
                    f"{BASE_URL}/api/v1/conversations",
                    headers=HEADERS,
                    params={"user_id": USER_ID},
                    json={
                        "title": "项目相关对话",
                        "project_id": project_id
                    }
                )
                print_test("在项目中创建对话", response.status_code == 200)
                
                # 3. 使用项目进行问答
                if response.status_code == 200:
                    conv_id = response.json()["id"]
                    await test_qa_with_history(client, project_id)
            else:
                print("   未找到项目，跳过项目集成测试")
        
    except Exception as e:
        print_test("项目集成", False, str(e))


async def main():
    """运行所有集成测试"""
    print("\n" + "🚀 " * 20)
    print("DPA对话历史功能集成测试")
    print("🚀 " * 20)
    print(f"后端地址: {BASE_URL}")
    print(f"用户ID: {USER_ID}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 健康检查
        await test_health_check(client)
        
        # 2. 对话管理
        conversation_result = await test_conversation_management(client)
        
        # 3. 带历史的问答
        qa_result = await test_qa_with_history(client)
        
        # 4. 对话消息管理
        if qa_result.get("conversation_id"):
            await test_conversation_messages(client, qa_result["conversation_id"])
        
        # 5. 对话导出
        if qa_result.get("conversation_id"):
            await test_conversation_export(client, qa_result["conversation_id"])
        
        # 6. 项目集成
        await test_project_integration(client)
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"总测试数: {test_results['total']}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    print(f"成功率: {test_results['passed']/test_results['total']*100:.1f}%")
    
    if test_results["errors"]:
        print("\n❌ 错误列表:")
        for error in test_results["errors"]:
            print(f"   - {error}")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 返回状态码
    return 0 if test_results["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)