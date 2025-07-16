#!/usr/bin/env python3
"""
诊断API基本功能
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}

async def diagnose():
    async with aiohttp.ClientSession() as session:
        print("1. 测试健康检查...")
        try:
            async with session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ API健康: {data['status']}")
                else:
                    print(f"   ❌ 健康检查失败: {resp.status}")
        except Exception as e:
            print(f"   ❌ 连接错误: {e}")
            return
        
        print("\n2. 测试项目列表...")
        try:
            async with session.get(f"{API_BASE}/api/v1/projects", headers=HEADERS) as resp:
                if resp.status == 200:
                    projects = await resp.json()
                    print(f"   ✅ 找到 {len(projects)} 个项目")
                    for i, p in enumerate(projects[:3]):
                        print(f"      - {p.get('name', 'unnamed')} ({p.get('id', 'no-id')})")
                else:
                    print(f"   ❌ 获取项目失败: {resp.status}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        print("\n3. 测试文档列表...")
        try:
            project_id = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"
            async with session.get(f"{API_BASE}/api/v1/documents?project_id={project_id}", headers=HEADERS) as resp:
                if resp.status == 200:
                    docs = await resp.json()
                    print(f"   ✅ 找到 {len(docs)} 个文档")
                    for i, d in enumerate(docs[:3]):
                        print(f"      - {d.get('filename', 'unnamed')} ({d.get('processing_status', 'unknown')})")
                else:
                    print(f"   ❌ 获取文档失败: {resp.status}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

async def main():
    print("🔍 API诊断工具")
    print("=" * 50)
    await diagnose()

if __name__ == "__main__":
    asyncio.run(main())