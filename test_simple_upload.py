#!/usr/bin/env python3
"""
简单的上传测试
"""

import asyncio
import aiohttp
import time
from pathlib import Path

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"

async def test_upload():
    # 创建测试文件
    test_file = Path(f"test_{int(time.time())}.txt")
    test_file.write_text(f"测试文档 - {time.time()}")
    
    print(f"测试文件: {test_file}")
    
    async with aiohttp.ClientSession() as session:
        # 只上传，不处理
        with open(test_file, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=test_file.name)
            data.add_field('upload_only', 'true')
            
            url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}"
            async with session.post(url, data=data, headers=HEADERS) as resp:
                print(f"响应状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print("响应内容:")
                    import json
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    error = await resp.text()
                    print(f"错误: {error}")
    
    # 清理
    test_file.unlink()

if __name__ == "__main__":
    asyncio.run(test_upload())