#!/usr/bin/env python3
"""
测试摘要API端点
"""

import requests
import json
import sys

def test_summary_api():
    """测试摘要API"""
    
    # 配置
    BASE_URL = "http://localhost:8200"
    USER_ID = "u1"
    
    # 测试文档ID（需要是实际存在的）
    TEST_DOC_ID = "test_doc_1"  # 这个需要替换为实际的文档ID
    
    headers = {
        "X-USER-ID": USER_ID,
        "Content-Type": "application/json"
    }
    
    print("🧪 测试摘要API端点...")
    
    # 测试1: 健康检查
    print("\n1. 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", headers=headers)
        print(f"健康检查: {response.status_code}")
        if response.status_code == 200:
            print("✅ 后端API正常运行")
        else:
            print("❌ 后端API异常")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端API: {e}")
        return False
    
    # 测试2: 获取文档列表
    print("\n2. 测试获取文档列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents", headers=headers)
        print(f"文档列表: {response.status_code}")
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ 找到 {len(docs.get('items', []))} 个文档")
            
            # 如果有文档，使用第一个文档ID进行测试
            if docs.get('items'):
                TEST_DOC_ID = docs['items'][0]['id']
                print(f"使用文档ID: {TEST_DOC_ID}")
            else:
                print("⚠️  没有文档可用于测试")
                return False
        else:
            print("❌ 获取文档列表失败")
            return False
    except Exception as e:
        print(f"❌ 获取文档列表异常: {e}")
        return False
    
    # 测试3: 获取文档摘要
    print("\n3. 测试获取文档摘要...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents/{TEST_DOC_ID}/summary", headers=headers)
        print(f"文档摘要: {response.status_code}")
        
        if response.status_code == 200:
            summary = response.json()
            print("✅ 成功获取文档摘要")
            print(f"文档名称: {summary.get('filename', 'N/A')}")
            print(f"摘要长度: {len(summary.get('summary', ''))}")
        elif response.status_code == 404:
            print("⚠️  文档摘要未生成")
            print("响应内容:", response.text)
        else:
            print(f"❌ 获取文档摘要失败: {response.status_code}")
            print("响应内容:", response.text)
    except Exception as e:
        print(f"❌ 获取文档摘要异常: {e}")
        return False
    
    # 测试4: 获取文档操作状态
    print("\n4. 测试获取文档操作状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents/{TEST_DOC_ID}/operations/status", headers=headers)
        print(f"操作状态: {response.status_code}")
        
        if response.status_code == 200:
            status = response.json()
            print("✅ 成功获取操作状态")
            print(f"摘要完成: {status.get('operations_summary', {}).get('summary_completed', False)}")
            print(f"索引完成: {status.get('operations_summary', {}).get('index_completed', False)}")
            print(f"分析完成: {status.get('operations_summary', {}).get('analysis_completed', False)}")
        else:
            print(f"❌ 获取操作状态失败: {response.status_code}")
            print("响应内容:", response.text)
    except Exception as e:
        print(f"❌ 获取操作状态异常: {e}")
        return False
    
    # 测试5: 获取文档分析
    print("\n5. 测试获取文档分析...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents/{TEST_DOC_ID}/analysis", headers=headers)
        print(f"文档分析: {response.status_code}")
        
        if response.status_code == 200:
            analysis = response.json()
            print("✅ 成功获取文档分析")
            print(f"分析深度: {analysis.get('analysis_depth', 'N/A')}")
            print(f"关键洞察数量: {len(analysis.get('result', {}).get('key_insights', []))}")
        elif response.status_code == 404:
            print("⚠️  文档分析未完成")
            print("响应内容:", response.text)
        else:
            print(f"❌ 获取文档分析失败: {response.status_code}")
            print("响应内容:", response.text)
    except Exception as e:
        print(f"❌ 获取文档分析异常: {e}")
        return False
    
    print("\n🎯 API测试完成")
    return True

if __name__ == "__main__":
    success = test_summary_api()
    sys.exit(0 if success else 1)