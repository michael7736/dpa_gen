#!/usr/bin/env python3
"""
诊断深度分析问题
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}

# 使用之前已上传的文档
DOCUMENT_ID = "5ec3e004-ab9c-40af-9ed3-0837fddfc628"

async def diagnose():
    async with aiohttp.ClientSession() as session:
        # 1. 检查文档是否存在
        print("1. 检查文档状态...")
        doc_url = f"{API_BASE}/api/v1/documents/{DOCUMENT_ID}"
        async with session.get(doc_url, headers=HEADERS) as resp:
            if resp.status == 200:
                doc_data = await resp.json()
                print(f"   文档存在: {doc_data['filename']}")
                print(f"   状态: {doc_data['processing_status']}")
            else:
                print(f"   ❌ 文档不存在: {resp.status}")
                return
        
        # 2. 检查最近的分析记录
        print("\n2. 检查分析记录...")
        analysis_url = f"{API_BASE}/api/v1/documents/{DOCUMENT_ID}/analysis"
        async with session.get(analysis_url, headers=HEADERS) as resp:
            if resp.status == 200:
                analysis_data = await resp.json()
                print(f"   分析ID: {analysis_data.get('analysis_id')}")
                print(f"   状态: {analysis_data.get('status')}")
                print(f"   创建时间: {analysis_data.get('created_at')}")
            else:
                print(f"   没有分析记录")
        
        # 3. 检查最近的管道
        print("\n3. 检查最近的管道...")
        pipelines_url = f"{API_BASE}/api/v1/pipelines?document_id={DOCUMENT_ID}"
        async with session.get(pipelines_url, headers=HEADERS) as resp:
            if resp.status == 200:
                pipelines = await resp.json()
                if pipelines:
                    latest = pipelines[0]
                    print(f"   管道ID: {latest['id']}")
                    print(f"   状态: 完成={latest['completed']}, 中断={latest['interrupted']}")
                    print(f"   进度: {latest['overall_progress']}%")
                    print(f"   当前阶段: {latest['current_stage']}")
                    
                    # 检查各阶段状态
                    if latest.get('stages'):
                        print("\n   阶段详情:")
                        for stage in latest['stages']:
                            print(f"   - {stage['stage_type']}: {stage['status']} ({stage['progress']}%)")
                            if stage.get('error'):
                                print(f"     错误: {stage['error']}")
        
        # 4. 直接启动一个新的分析
        print("\n4. 尝试启动新的分析...")
        exec_url = f"{API_BASE}/api/v1/documents/{DOCUMENT_ID}/operations/analysis/execute"
        async with session.post(exec_url, headers=HEADERS) as resp:
            print(f"   响应状态: {resp.status}")
            if resp.status == 200:
                result = await resp.json()
                print(f"   管道ID: {result.get('pipeline_id')}")
            else:
                error_text = await resp.text()
                print(f"   错误: {error_text}")

async def main():
    print("🔍 深度分析诊断工具")
    print("=" * 50)
    await diagnose()

if __name__ == "__main__":
    asyncio.run(main())