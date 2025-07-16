#!/usr/bin/env python3
"""
简化的认知API测试 - 适配8001端口和dpa_gen环境
"""

import requests
import json

API_BASE = "http://localhost:8001"

def test_basic_health():
    """测试基础健康检查"""
    print("🔍 测试基础API健康检查...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 基础API健康检查通过")
            return True
        else:
            print(f"❌ 基础API健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务器: {e}")
        return False

def test_cognitive_health():
    """测试认知系统健康检查"""
    print("🧠 测试认知系统健康检查...")
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/cognitive/health", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 认知系统健康检查通过: {result.get('status', 'unknown')}")
            components = result.get('components', {})
            for name, status in components.items():
                print(f"   {name}: {status}")
            return True
        else:
            print(f"❌ 认知系统健康检查失败: {response.status_code}")
            if response.text:
                print(f"   错误详情: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 认知系统健康检查异常: {e}")
        return False

def test_simple_cognitive_chat():
    """测试简单的认知对话"""
    print("💬 测试认知对话功能...")
    
    try:
        # 构建请求数据
        request_data = {
            "message": "你好，请简单介绍一下认知系统的功能",
            "project_id": "test_project",
            "use_memory": False,  # 简化测试
            "max_results": 5
        }
        
        # FastAPI期望请求体包含在一个名为request的字段中
        data = {"request": request_data}
        
        headers = {
            "Content-Type": "application/json",
            "X-USER-ID": "test_user"
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/cognitive/chat",
            json=data,  # 发送包装后的数据
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 认知对话功能正常")
            print(f"   对话ID: {result.get('conversation_id', 'unknown')}")
            print(f"   策略: {result.get('strategy_used', 'unknown')}")
            print(f"   置信度: {result.get('confidence_score', 0):.3f}")
            print(f"   处理时间: {result.get('processing_time', 0):.3f}s")
            print(f"   响应预览: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ 认知对话功能失败: {response.status_code}")
            if response.text:
                print(f"   错误详情: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 认知对话功能异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 DPA认知系统API简化测试")
    print("=" * 50)
    print(f"测试环境:")
    print(f"  - 后端API: {API_BASE}")
    print(f"  - 预期环境: dpa_gen conda环境")
    print(f"  - 前端地址: http://localhost:8031")
    print("")
    
    # 运行测试
    tests = [
        ("基础健康检查", test_basic_health),
        ("认知系统健康检查", test_cognitive_health),
        ("认知对话功能", test_simple_cognitive_chat)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        success = test_func()
        results.append((test_name, success))
        print("")
    
    # 总结
    print("=" * 50)
    print("📊 测试结果总结:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！认知系统API准备就绪")
    elif passed > 0:
        print("⚠️  部分测试通过，系统部分可用")
    else:
        print("❌ 所有测试失败，请检查服务器状态")
    
    return passed == len(results)

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未预期错误: {e}")
        exit(1)