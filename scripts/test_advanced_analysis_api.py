#!/usr/bin/env python3
"""
测试高级文档分析API集成
验证API端点是否正常工作
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from uuid import uuid4

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试数据
TEST_PROJECT_ID = "123e4567-e89b-12d3-a456-426614174000"  # 需要替换为实际项目ID
TEST_DOCUMENT_ID = "456e7890-e89b-12d3-a456-426614174000"  # 需要替换为实际文档ID
TEST_USER_ID = "test_user"


async def test_quick_analysis():
    """测试快速文本分析"""
    print("\n=== 测试快速文本分析 ===")
    
    test_text = """
    人工智能（AI）正在彻底改变教育领域。通过个性化学习系统，AI能够根据每个学生的学习速度和风格定制教育内容。
    研究表明，使用AI辅助学习的学生平均成绩提高了30%。然而，这也带来了新的挑战，如数据隐私和教师角色的转变。
    未来，混合式学习模式将成为主流，结合AI的优势和人类教师的创造力与同理心。
    """
    
    payload = {
        "content": test_text,
        "title": "AI教育应用测试",
        "analysis_depth": "basic",
        "analysis_goal": "理解AI在教育中的应用和影响"
    }
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/analysis/analyze-text?user_id={TEST_USER_ID}"
        async with session.post(url, json=payload) as response:
            print(f"状态码: {response.status}")
            result = await response.json()
            print("响应:", json.dumps(result, indent=2, ensure_ascii=False))
            return response.status == 200


async def test_start_analysis():
    """测试启动文档分析"""
    print("\n=== 测试启动文档分析 ===")
    
    payload = {
        "document_id": TEST_DOCUMENT_ID,
        "project_id": TEST_PROJECT_ID,
        "analysis_depth": "standard",
        "analysis_goal": "深入理解文档内容并提取关键洞察"
    }
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/analysis/start?user_id={TEST_USER_ID}"
        async with session.post(url, json=payload) as response:
            print(f"状态码: {response.status}")
            result = await response.json()
            print("响应:", json.dumps(result, indent=2, ensure_ascii=False))
            
            if response.status == 200:
                return result.get("analysis_id")
            return None


async def test_get_status(analysis_id: str):
    """测试获取分析状态"""
    print(f"\n=== 测试获取分析状态: {analysis_id} ===")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/analysis/status/{analysis_id}"
        async with session.get(url) as response:
            print(f"状态码: {response.status}")
            result = await response.json()
            print("响应:", json.dumps(result, indent=2, ensure_ascii=False))
            return response.status == 200


async def test_list_analyses():
    """测试列出分析任务"""
    print("\n=== 测试列出分析任务 ===")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/analysis/list?user_id={TEST_USER_ID}&page=1&per_page=10"
        async with session.get(url) as response:
            print(f"状态码: {response.status}")
            result = await response.json()
            print("响应:", json.dumps(result, indent=2, ensure_ascii=False))
            return response.status == 200


async def test_get_templates():
    """测试获取分析模板"""
    print("\n=== 测试获取分析模板 ===")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/analysis/templates"
        async with session.get(url) as response:
            print(f"状态码: {response.status}")
            result = await response.json()
            print("响应:", json.dumps(result, indent=2, ensure_ascii=False))
            return response.status == 200


async def main():
    """运行所有测试"""
    print("开始测试高级文档分析API...")
    print(f"基础URL: {BASE_URL}")
    print(f"测试时间: {datetime.now().isoformat()}")
    
    # 测试结果
    results = []
    
    # 1. 测试获取模板
    try:
        result = await test_get_templates()
        results.append(("获取分析模板", result))
    except Exception as e:
        print(f"错误: {e}")
        results.append(("获取分析模板", False))
    
    # 2. 测试快速分析
    try:
        result = await test_quick_analysis()
        results.append(("快速文本分析", result))
    except Exception as e:
        print(f"错误: {e}")
        results.append(("快速文本分析", False))
    
    # 3. 测试启动分析（需要有效的文档ID）
    # analysis_id = None
    # try:
    #     analysis_id = await test_start_analysis()
    #     results.append(("启动文档分析", analysis_id is not None))
    # except Exception as e:
    #     print(f"错误: {e}")
    #     results.append(("启动文档分析", False))
    
    # 4. 测试获取状态（如果有分析ID）
    # if analysis_id:
    #     try:
    #         result = await test_get_status(analysis_id)
    #         results.append(("获取分析状态", result))
    #     except Exception as e:
    #         print(f"错误: {e}")
    #         results.append(("获取分析状态", False))
    
    # 5. 测试列出分析
    try:
        result = await test_list_analyses()
        results.append(("列出分析任务", result))
    except Exception as e:
        print(f"错误: {e}")
        results.append(("列出分析任务", False))
    
    # 打印总结
    print("\n" + "="*50)
    print("测试结果总结:")
    print("="*50)
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    print(f"\n总计: {success_count}/{total_count} 测试通过")


if __name__ == "__main__":
    asyncio.run(main())