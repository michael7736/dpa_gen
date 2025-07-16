#!/usr/bin/env python3
"""
前后端集成测试
测试前端页面和后端API的完整集成
"""

import asyncio
import httpx
import json
from datetime import datetime
from urllib.parse import quote

# 配置
BACKEND_URL = "http://localhost:8200"
FRONTEND_URL = "http://localhost:8230"
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
    print(f"🌐 {title}")
    print("=" * 60)


def print_test(name: str, passed: bool, error: str = None, details: str = None):
    """打印测试结果"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {error}")
        print(f"❌ {name}")
        if error:
            print(f"   错误: {error}")


async def test_frontend_accessibility(client: httpx.AsyncClient):
    """测试前端页面可访问性"""
    print_header("前端页面可访问性")
    
    pages = [
        ("主页", "/"),
        ("项目页面", "/projects"),
        ("文档管理", "/documents"),
        ("智能问答", "/chat"),
        ("设置页面", "/settings"),
        ("AAG分析引擎", "/aag"),
        ("AI副驾驶", "/copilot")
    ]
    
    for name, path in pages:
        try:
            response = await client.get(f"{FRONTEND_URL}{path}")
            
            # 检查页面是否正确加载
            is_valid = (
                response.status_code == 200 and
                "DPA智能知识引擎" in response.text and
                "<!DOCTYPE html>" in response.text
            )
            
            print_test(name, is_valid, details=f"状态码: {response.status_code}")
            
        except Exception as e:
            print_test(name, False, str(e))


async def test_api_connectivity(client: httpx.AsyncClient):
    """测试API连接性"""
    print_header("API连接性测试")
    
    # 从前端到后端的关键API调用
    api_tests = [
        ("健康检查", "GET", "/health", None),
        ("项目列表", "GET", "/api/v1/projects", HEADERS),
        ("用户信息", "GET", "/api/v1/user/profile", HEADERS),
        ("系统状态", "GET", "/api/v1/system/status", HEADERS)
    ]
    
    for name, method, endpoint, headers in api_tests:
        try:
            if method == "GET":
                response = await client.get(f"{BACKEND_URL}{endpoint}", headers=headers or {})
            else:
                response = await client.post(f"{BACKEND_URL}{endpoint}", headers=headers or {})
            
            print_test(
                name,
                response.status_code in [200, 201],
                details=f"状态码: {response.status_code}"
            )
            
        except Exception as e:
            print_test(name, False, str(e))


async def test_cors_configuration(client: httpx.AsyncClient):
    """测试CORS配置"""
    print_header("CORS配置测试")
    
    try:
        # 模拟前端发起的预检请求
        response = await client.options(
            f"{BACKEND_URL}/api/v1/projects",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-USER-ID,Content-Type"
            }
        )
        
        cors_configured = (
            response.status_code == 200 or 
            "Access-Control-Allow-Origin" in response.headers
        )
        
        print_test("CORS预检请求", cors_configured)
        
        # 测试实际跨域请求
        response = await client.get(
            f"{BACKEND_URL}/api/v1/projects",
            headers={
                **HEADERS,
                "Origin": FRONTEND_URL
            }
        )
        
        print_test(
            "跨域GET请求",
            response.status_code == 200,
            details=f"状态码: {response.status_code}"
        )
        
    except Exception as e:
        print_test("CORS配置", False, str(e))


async def test_data_flow(client: httpx.AsyncClient):
    """测试数据流（前端<->后端）"""
    print_header("数据流测试")
    
    try:
        # 1. 获取项目数据（模拟前端请求）
        response = await client.get(f"{BACKEND_URL}/api/v1/projects", headers=HEADERS)
        
        if response.status_code == 200:
            projects = response.json()
            print_test(
                "获取项目数据",
                True,
                details=f"返回 {len(projects)} 个项目"
            )
            
            # 2. 如果有项目，测试获取项目详情
            if projects:
                project_id = projects[0]["id"]
                response = await client.get(
                    f"{BACKEND_URL}/api/v1/projects/{project_id}",
                    headers=HEADERS
                )
                print_test(
                    "项目详情获取",
                    response.status_code == 200,
                    details=f"项目ID: {project_id}"
                )
                
                # 3. 获取项目文档
                response = await client.get(
                    f"{BACKEND_URL}/api/v1/documents",
                    headers=HEADERS,
                    params={"project_id": project_id}
                )
                print_test(
                    "项目文档获取",
                    response.status_code == 200,
                    details=f"状态码: {response.status_code}"
                )
        else:
            print_test("获取项目数据", False, f"状态码: {response.status_code}")
            
    except Exception as e:
        print_test("数据流测试", False, str(e))


async def test_authentication_flow(client: httpx.AsyncClient):
    """测试认证流程"""
    print_header("认证流程测试")
    
    try:
        # 1. 测试无认证请求
        response = await client.get(f"{BACKEND_URL}/api/v1/projects")
        print_test(
            "无认证访问",
            response.status_code in [401, 403, 422],  # 应该被拒绝
            details=f"状态码: {response.status_code}"
        )
        
        # 2. 测试有效认证
        response = await client.get(f"{BACKEND_URL}/api/v1/projects", headers=HEADERS)
        print_test(
            "有效认证访问",
            response.status_code == 200,
            details=f"用户ID: {USER_ID}"
        )
        
        # 3. 测试无效认证
        invalid_headers = {"X-USER-ID": "invalid_user_123"}
        response = await client.get(f"{BACKEND_URL}/api/v1/projects", headers=invalid_headers)
        print_test(
            "无效认证处理",
            response.status_code in [200, 401, 403],  # 可能允许或拒绝
            details=f"状态码: {response.status_code}"
        )
        
    except Exception as e:
        print_test("认证流程", False, str(e))


async def test_error_handling(client: httpx.AsyncClient):
    """测试错误处理"""
    print_header("错误处理测试")
    
    error_scenarios = [
        ("不存在的端点", "GET", "/api/v1/nonexistent", None, [404]),
        ("无效的项目ID", "GET", "/api/v1/projects/invalid-id", HEADERS, [400, 404, 422]),
        ("无效的JSON", "POST", "/api/v1/projects", HEADERS, [400, 422]),
        ("缺少必需参数", "POST", "/api/v1/qa/answer", HEADERS, [400, 422])
    ]
    
    for name, method, endpoint, headers, expected_codes in error_scenarios:
        try:
            if method == "GET":
                response = await client.get(f"{BACKEND_URL}{endpoint}", headers=headers or {})
            elif method == "POST":
                if "invalid" in name.lower():
                    # 发送无效JSON
                    response = await client.post(
                        f"{BACKEND_URL}{endpoint}",
                        headers=headers or {},
                        content="{invalid json"
                    )
                else:
                    # 发送空JSON
                    response = await client.post(
                        f"{BACKEND_URL}{endpoint}",
                        headers=headers or {},
                        json={}
                    )
            
            print_test(
                name,
                response.status_code in expected_codes,
                details=f"状态码: {response.status_code} (期望: {expected_codes})"
            )
            
        except Exception as e:
            print_test(name, False, str(e))


async def test_performance_metrics(client: httpx.AsyncClient):
    """测试性能指标"""
    print_header("性能指标测试")
    
    try:
        # 测试API响应时间
        start_time = asyncio.get_event_loop().time()
        response = await client.get(f"{BACKEND_URL}/health")
        health_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        print_test(
            "健康检查响应时间",
            health_time < 1000,  # 小于1秒
            details=f"{health_time:.1f}ms"
        )
        
        # 测试项目列表响应时间
        start_time = asyncio.get_event_loop().time()
        response = await client.get(f"{BACKEND_URL}/api/v1/projects", headers=HEADERS)
        projects_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        print_test(
            "项目列表响应时间",
            projects_time < 2000,  # 小于2秒
            details=f"{projects_time:.1f}ms"
        )
        
        # 测试前端页面加载时间
        start_time = asyncio.get_event_loop().time()
        response = await client.get(f"{FRONTEND_URL}/projects")
        frontend_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        print_test(
            "前端页面加载时间",
            frontend_time < 3000,  # 小于3秒
            details=f"{frontend_time:.1f}ms"
        )
        
    except Exception as e:
        print_test("性能指标", False, str(e))


async def main():
    """运行前后端集成测试"""
    print("\n" + "🌐" * 20)
    print("DPA前后端集成测试")
    print("🌐" * 20)
    print(f"前端地址: {FRONTEND_URL}")
    print(f"后端地址: {BACKEND_URL}")
    print(f"用户ID: {USER_ID}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 前端页面可访问性
        await test_frontend_accessibility(client)
        
        # 2. API连接性
        await test_api_connectivity(client)
        
        # 3. CORS配置
        await test_cors_configuration(client)
        
        # 4. 数据流测试
        await test_data_flow(client)
        
        # 5. 认证流程
        await test_authentication_flow(client)
        
        # 6. 错误处理
        await test_error_handling(client)
        
        # 7. 性能指标
        await test_performance_metrics(client)
    
    # 打印测试总结
    print_header("📊 前后端集成测试总结")
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
    
    # 集成质量评估
    if success_rate >= 90:
        print("\n🎉 集成质量: 优秀 - 前后端完美集成")
    elif success_rate >= 80:
        print("\n✅ 集成质量: 良好 - 主要功能集成正常")
    elif success_rate >= 70:
        print("\n⚠️  集成质量: 一般 - 基本集成正常，有待改进")
    else:
        print("\n❌ 集成质量: 需要改进 - 存在较多集成问题")


if __name__ == "__main__":
    asyncio.run(main())