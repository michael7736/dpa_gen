#!/usr/bin/env python
"""
测试API限流和版本控制功能
"""

import asyncio
import time
from typing import Dict, List
import httpx

from ..src.config.settings import get_settings

settings = get_settings()


class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        
    async def close(self):
        await self.client.aclose()
        
    async def test_rate_limiting(self):
        """测试限流功能"""
        print("\n=== 测试限流功能 ===")
        
        # 1. 测试正常请求
        print("\n1. 测试正常请求（无限流）:")
        for i in range(5):
            response = await self.client.get("/api/v1/demo/basic")
            print(f"   请求 {i+1}: {response.status_code}")
            
        # 2. 测试严格限流（10次/分钟）
        print("\n2. 测试严格限流端点（10次/分钟）:")
        for i in range(15):
            try:
                response = await self.client.get("/api/v1/demo/limited")
                if response.status_code == 200:
                    print(f"   请求 {i+1}: ✅ 成功")
                elif response.status_code == 429:
                    data = response.json()
                    print(f"   请求 {i+1}: ❌ 限流 - {data['detail']['message']}")
                    print(f"   重试时间: {response.headers.get('Retry-After')}秒")
                    break
            except Exception as e:
                print(f"   请求 {i+1}: ❌ 错误 - {e}")
                
        # 3. 测试限流头部
        print("\n3. 检查限流响应头:")
        response = await self.client.get("/api/v1/demo/rate-limit-test")
        if response.status_code == 200:
            data = response.json()
            print(f"   限流配置: {data['headers']}")
            
    async def test_api_versioning(self):
        """测试API版本控制"""
        print("\n=== 测试API版本控制 ===")
        
        # 1. 测试默认版本
        print("\n1. 测试默认版本:")
        response = await self.client.get("/api/v1/demo/version-test")
        if response.status_code == 200:
            data = response.json()
            print(f"   当前版本: {data['current_version']}")
            print(f"   可用特性: {list(data['available_features'].keys())}")
            
        # 2. 测试通过头部指定版本
        print("\n2. 测试通过头部指定版本:")
        headers = {"X-API-Version": "v2"}
        response = await self.client.get("/api/demo/version-test", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   请求版本: v2")
            print(f"   响应版本: {data['current_version']}")
            print(f"   新增特性: {[k for k, v in data['available_features'].items() if v]}")
            
        # 3. 测试版本要求
        print("\n3. 测试版本要求的端点:")
        # 使用V1访问V2端点
        response = await self.client.get("/api/v1/demo/v2-feature")
        if response.status_code == 400:
            print(f"   V1访问V2端点: ❌ {response.json()['detail']}")
            
        # 使用V2访问V2端点
        response = await self.client.get("/api/v2/demo/v2-feature", headers=headers)
        if response.status_code == 200:
            print(f"   V2访问V2端点: ✅ 成功")
            
        # 4. 测试弃用端点
        print("\n4. 测试弃用端点:")
        response = await self.client.get("/api/v1/demo/deprecated")
        if response.status_code == 200:
            print(f"   状态: {response.status_code}")
            print(f"   弃用标记: {response.headers.get('X-API-Deprecated')}")
            print(f"   停用日期: {response.headers.get('X-API-Sunset')}")
            print(f"   替代端点: {response.headers.get('X-API-Alternative')}")
            
    async def test_combined_features(self):
        """测试限流和版本控制的组合"""
        print("\n=== 测试组合功能 ===")
        
        # 测试不同版本的限流配置
        print("\n测试不同版本的限流配置:")
        
        versions = ["v1", "v2"]
        for version in versions:
            print(f"\n版本 {version}:")
            headers = {"X-API-Version": version} if version != "v1" else {}
            
            # 快速发送多个请求
            success_count = 0
            rate_limited_count = 0
            
            for i in range(20):
                response = await self.client.get(
                    f"/api/{version}/demo/limited",
                    headers=headers
                )
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
                    
                # 短暂延迟
                await asyncio.sleep(0.1)
                
            print(f"   成功请求: {success_count}")
            print(f"   被限流请求: {rate_limited_count}")


async def main():
    """主测试函数"""
    print("=== DPA API限流和版本控制测试 ===")
    
    # 确保API服务正在运行
    print("\n检查API服务...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code != 200:
                print("❌ API服务未运行，请先启动服务")
                return
            print("✅ API服务正在运行")
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        print("请先运行: uvicorn src.api.main:app --reload")
        return
        
    # 运行测试
    tester = APITester()
    try:
        await tester.test_rate_limiting()
        await tester.test_api_versioning()
        await tester.test_combined_features()
        
        print("\n✅ 所有测试完成")
        
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())