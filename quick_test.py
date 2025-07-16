#!/usr/bin/env python3
"""
快速测试API响应
"""

import requests
import time

def quick_test():
    print("🔍 快速测试API服务器...")
    
    # 测试根端点
    try:
        print("测试根端点...")
        start = time.time()
        response = requests.get("http://localhost:8001/", timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ 根端点响应正常 ({elapsed:.2f}s)")
            result = response.json()
            print(f"   服务名称: {result.get('name', 'unknown')}")
            print(f"   版本: {result.get('version', 'unknown')}")
        else:
            print(f"❌ 根端点响应异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 根端点测试失败: {e}")
        return False
    
    # 测试API文档
    try:
        print("\n测试API文档端点...")
        start = time.time()
        response = requests.get("http://localhost:8001/docs", timeout=30)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ API文档可访问 ({elapsed:.2f}s)")
        else:
            print(f"❌ API文档访问异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API文档测试失败: {e}")
    
    return True

if __name__ == "__main__":
    quick_test()