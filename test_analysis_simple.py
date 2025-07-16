#!/usr/bin/env python3
"""
简化的深度分析测试
"""

import asyncio
import aiohttp
import time
import json

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}

# 使用之前已上传的文档
DOCUMENT_ID = "5ec3e004-ab9c-40af-9ed3-0837fddfc628"

async def test_deep_analysis():
    """测试深度分析功能"""
    print("🧠 测试深度分析功能")
    print("=" * 50)
    print(f"文档ID: {DOCUMENT_ID}")
    
    async with aiohttp.ClientSession() as session:
        # 1. 检查文档状态
        print("\n1️⃣ 检查文档状态...")
        status_url = f"{API_BASE}/api/v1/documents/{DOCUMENT_ID}/operations/status"
        async with session.get(status_url, headers=HEADERS) as resp:
            if resp.status == 200:
                status_data = await resp.json()
                print(f"  📄 文档状态: {status_data['document_status']}")
                print(f"  ✅ 摘要完成: {status_data['operations_summary']['summary_completed']}")
                print(f"  🔍 索引完成: {status_data['operations_summary']['index_completed']}")
                print(f"  🧠 分析完成: {status_data['operations_summary']['analysis_completed']}")
            else:
                print(f"  ❌ 获取状态失败: {resp.status}")
                return
        
        # 2. 启动深度分析
        print("\n2️⃣ 启动深度分析任务...")
        start_time = time.time()
        
        analysis_url = f"{API_BASE}/api/v1/documents/{DOCUMENT_ID}/operations/analysis/execute"
        async with session.post(analysis_url, headers=HEADERS) as resp:
            if resp.status == 200:
                result = await resp.json()
                pipeline_id = result.get('pipeline_id')
                print(f"  ✅ 分析任务启动成功")
                print(f"  🔧 Pipeline ID: {pipeline_id}")
                
                # 3. 轮询检查状态（不使用WebSocket）
                if pipeline_id:
                    print("\n3️⃣ 监控分析进度...")
                    for i in range(60):  # 最多等待5分钟
                        await asyncio.sleep(5)  # 每5秒检查一次
                        
                        # 检查管道状态
                        pipeline_url = f"{API_BASE}/api/v1/pipelines/{pipeline_id}/status"
                        async with session.get(pipeline_url, headers=HEADERS) as status_resp:
                            if status_resp.status == 200:
                                pipeline_status = await status_resp.json()
                                progress = pipeline_status.get('overall_progress', 0)
                                current_stage = pipeline_status.get('current_stage', 'unknown')
                                completed = pipeline_status.get('completed', False)
                                
                                print(f"  📊 进度: {progress:.1f}% - {current_stage}")
                                
                                if completed:
                                    duration = time.time() - start_time
                                    print(f"\n✅ 分析完成!")
                                    print(f"⏱️  总耗时: {duration:.2f}秒")
                                    
                                    # 4. 获取分析结果
                                    print("\n4️⃣ 获取分析结果...")
                                    analysis_result_url = f"{API_BASE}/api/v1/documents/{DOCUMENT_ID}/analysis"
                                    async with session.get(analysis_result_url, headers=HEADERS) as analysis_resp:
                                        if analysis_resp.status == 200:
                                            analysis_data = await analysis_resp.json()
                                            
                                            print(f"\n📊 分析结果概要:")
                                            print(f"  📋 分析ID: {analysis_data.get('analysis_id', 'N/A')}")
                                            print(f"  🔍 分析深度: {analysis_data.get('analysis_depth', 'N/A')}")
                                            print(f"  📈 状态: {analysis_data.get('status', 'N/A')}")
                                            
                                            result = analysis_data.get('result', {})
                                            if result:
                                                print(f"  💡 洞察数量: {len(result.get('key_insights', []))}")
                                                print(f"  🎯 行动项数: {len(result.get('action_items', []))}")
                                                
                                                if result.get('executive_summary'):
                                                    print(f"\n📝 执行摘要:")
                                                    print(f"  {result['executive_summary'][:200]}...")
                                                
                                                print(f"\n✅ 深度分析功能已修复并正常工作!")
                                            else:
                                                print(f"  ⚠️  分析结果为空")
                                        else:
                                            error_text = await analysis_resp.text()
                                            print(f"  ❌ 获取分析结果失败: {analysis_resp.status}")
                                            print(f"  错误: {error_text}")
                                    return
                                
                                # 检查是否有错误
                                if pipeline_status.get('stages'):
                                    for stage in pipeline_status['stages']:
                                        if stage.get('stage_type') == 'analysis' and stage.get('status') == 'failed':
                                            print(f"\n❌ 分析失败: {stage.get('error')}")
                                            return
                    
                    print(f"\n❌ 分析超时（5分钟）")
            else:
                error_text = await resp.text()
                print(f"  ❌ 启动分析失败: {resp.status}")
                print(f"  错误: {error_text}")

async def main():
    await test_deep_analysis()

if __name__ == "__main__":
    print("🚀 启动深度分析功能测试（简化版）...")
    print(f"API服务器: {API_BASE}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    asyncio.run(main())