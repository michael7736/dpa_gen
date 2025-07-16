#!/usr/bin/env python3
"""
当前系统集成测试
测试主要的API端点和功能
"""

import asyncio
import httpx
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"
HEADERS = {"X-USER-ID": USER_ID}

# 测试结果统计
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
        response = await client.get(f"{BASE_URL}/health")
        print_test("主健康检查", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   服务: {data.get('service')}")
            print(f"   状态: {data.get('status')}")
            print(f"   版本: {data.get('version')}")
            
    except Exception as e:
        print_test("健康检查", False, str(e))


async def test_projects(client: httpx.AsyncClient) -> str:
    """测试项目管理"""
    print_header("项目管理")
    
    project_id = None
    
    try:
        # 获取项目列表
        response = await client.get(
            f"{BASE_URL}/api/v1/projects",
            headers=HEADERS
        )
        print_test("获取项目列表", response.status_code == 200)
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   项目数量: {len(projects)}")
            if projects:
                project_id = projects[0]["id"]
                print(f"   第一个项目: {projects[0]['name']} (ID: {project_id})")
                
    except Exception as e:
        print_test("项目管理", False, str(e))
        
    return project_id


async def test_documents(client: httpx.AsyncClient, project_id: str):
    """测试文档管理"""
    print_header("文档管理")
    
    if not project_id:
        print("⚠️  跳过文档测试（无项目ID）")
        return
        
    try:
        # 获取文档列表
        response = await client.get(
            f"{BASE_URL}/api/v1/documents",
            headers=HEADERS,
            params={"project_id": project_id}
        )
        print_test("获取文档列表", response.status_code == 200)
        
        if response.status_code == 200:
            documents = response.json()
            print(f"   文档数量: {len(documents)}")
            if documents:
                print(f"   第一个文档: {documents[0]['file_name']}")
                
    except Exception as e:
        print_test("文档管理", False, str(e))


async def test_aag_endpoints(client: httpx.AsyncClient):
    """测试AAG分析端点"""
    print_header("AAG智能分析")
    
    # 快速略读请求
    skim_request = {
        "document_id": "test_doc",
        "document_content": "这是一个测试文档，用于验证AAG分析功能。深度学习是机器学习的一个分支。",
        "document_type": "article"
    }
    
    # 摘要请求
    summary_request = {
        "document_id": "test_doc",
        "document_content": "这是一个测试文档，用于验证AAG分析功能。深度学习是机器学习的一个分支。",
        "summary_level": "level_2"
    }
    
    # 知识图谱请求
    kg_request = {
        "document_id": "test_doc",
        "document_content": "这是一个测试文档，用于验证AAG分析功能。深度学习是机器学习的一个分支。",
        "extraction_mode": "quick"
    }
    
    # 大纲请求
    outline_request = {
        "document_id": "test_doc",
        "document_content": "这是一个测试文档，用于验证AAG分析功能。深度学习是机器学习的一个分支。",
        "outline_mode": "hierarchical"
    }
    
    # 深度分析请求
    deep_request = {
        "document_id": "test_doc",
        "document_content": "这是一个测试文档，用于验证AAG分析功能。深度学习是机器学习的一个分支。",
        "analysis_type": "technological"
    }
    
    # 测试各个AAG端点
    endpoints = [
        ("快速略读", "/api/v1/aag/skim", "skim_request", skim_request),
        ("摘要生成", "/api/v1/aag/summary", "summary_request", summary_request),
        ("知识图谱", "/api/v1/aag/knowledge-graph", "kg_request", kg_request),
        ("大纲提取", "/api/v1/aag/outline", "outline_request", outline_request),
        ("深度分析", "/api/v1/aag/deep-analysis", "analysis_request", deep_request)
    ]
    
    for name, endpoint, param_name, request_data in endpoints:
        try:
            # AAG端点需要包装请求参数
            wrapped_data = {param_name: request_data}
            response = await client.post(
                f"{BASE_URL}{endpoint}",
                headers=HEADERS,
                json=wrapped_data
            )
            # AAG端点通常返回200或模拟数据
            print_test(name, response.status_code in [200, 201])
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"   ✓ 分析成功")
                    
        except Exception as e:
            print_test(name, False, str(e))


async def test_simple_qa(client: httpx.AsyncClient, project_id: str):
    """测试简单问答功能"""
    print_header("问答功能")
    
    try:
        # 测试问答
        qa_data = {
            "question": "什么是深度学习？",
            "project_id": project_id or "test_project"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/qa/answer",
            headers=HEADERS,
            json=qa_data
        )
        print_test("基础问答", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   回答预览: {data.get('answer', '')[:100]}...")
            print(f"   置信度: {data.get('confidence', 'N/A')}")
            
    except Exception as e:
        print_test("问答功能", False, str(e))


async def main():
    """运行所有测试"""
    print("\n" + "🚀" * 20)
    print("DPA系统集成测试")
    print("🚀" * 20)
    print(f"后端地址: {BASE_URL}")
    print(f"用户ID: {USER_ID}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 健康检查
        await test_health_check(client)
        
        # 2. 项目管理
        project_id = await test_projects(client)
        
        # 3. 文档管理
        await test_documents(client, project_id)
        
        # 4. AAG分析功能
        await test_aag_endpoints(client)
        
        # 5. 问答功能
        await test_simple_qa(client, project_id)
    
    # 打印测试总结
    print_header("📊 测试总结")
    print(f"总测试数: {test_results['total']}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    
    if test_results['errors']:
        print("\n❌ 错误列表:")
        for error in test_results['errors']:
            print(f"   - {error}")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())