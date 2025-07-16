#!/usr/bin/env python3
"""
测试带处理的上传
"""

import asyncio
import aiohttp
import time
from pathlib import Path

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"

async def test_upload_with_processing():
    # 创建测试文件
    test_content = f"""# 测试文档 {time.time()}

这是一个测试文档，用于验证文档处理流程。

## 内容概述
- 主题：人工智能技术
- 重点：深度学习应用
- 目标：验证系统功能

## 技术要点
1. 神经网络架构
2. 训练优化方法
3. 实际应用案例

## 结论
深度学习是AI发展的重要方向。
"""
    
    test_file = Path(f"test_doc_{int(time.time())}.md")
    test_file.write_text(test_content)
    
    print(f"📄 测试文件: {test_file}")
    
    async with aiohttp.ClientSession() as session:
        # 上传并处理
        with open(test_file, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=test_file.name)
            data.add_field('upload_only', 'false')
            data.add_field('generate_summary', 'true')
            data.add_field('create_index', 'true')
            data.add_field('deep_analysis', 'false')  # 暂时不测试深度分析
            
            url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}"
            async with session.post(url, data=data, headers=HEADERS) as resp:
                print(f"📤 响应状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    document_id = result['document_id']
                    pipeline_data = result.get('processing_pipeline')
                    
                    print(f"✅ 上传成功")
                    print(f"  文档ID: {document_id}")
                    print(f"  消息: {result['message']}")
                    
                    if pipeline_data:
                        pipeline_id = pipeline_data['pipeline_id']
                        print(f"  管道ID: {pipeline_id}")
                        print(f"  阶段数: {len(pipeline_data.get('stages', []))}")
                        
                        # 监控处理进度
                        print("\n⏳ 监控处理进度...")
                        for i in range(60):  # 最多等待5分钟
                            await asyncio.sleep(5)
                            
                            # 检查管道状态
                            status_url = f"{API_BASE}/api/v1/pipelines/{pipeline_id}/status"
                            async with session.get(status_url, headers=HEADERS) as status_resp:
                                if status_resp.status == 200:
                                    status = await status_resp.json()
                                    progress = status.get('overall_progress', 0)
                                    print(f"  进度: {progress:.1f}%")
                                    
                                    if status.get('completed'):
                                        print("✅ 处理完成！")
                                        
                                        # 获取摘要
                                        summary_url = f"{API_BASE}/api/v1/documents/{document_id}/summary"
                                        async with session.get(summary_url, headers=HEADERS) as summary_resp:
                                            if summary_resp.status == 200:
                                                summary_data = await summary_resp.json()
                                                print(f"\n📝 摘要: {summary_data['summary']}")
                                                print(f"🔑 关键词: {', '.join(summary_data['keywords'])}")
                                        break
                else:
                    error = await resp.text()
                    print(f"❌ 错误: {error}")
    
    # 清理
    test_file.unlink()
    print(f"\n🧹 已清理测试文件")

if __name__ == "__main__":
    asyncio.run(test_upload_with_processing())