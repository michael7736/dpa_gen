#!/usr/bin/env python3
"""
测试深度分析功能修复
"""

import asyncio
import aiohttp
import time
import json
import websockets

API_BASE = "http://localhost:8200"
WS_BASE = "ws://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
USER_ID = "243588ff-459d-45b8-b77b-09aec3946a64"

# 使用之前已上传的文档
DOCUMENT_ID = "5ec3e004-ab9c-40af-9ed3-0837fddfc628"

async def monitor_progress_with_websocket(pipeline_id: str, timeout: int = 300):
    """通过WebSocket监控处理进度"""
    ws_url = f"{WS_BASE}/api/v1/ws/{USER_ID}?connection_id=test_analysis_{int(time.time())}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            # 订阅管道进度
            subscribe_message = {
                "type": "subscribe_pipeline",
                "pipeline_id": pipeline_id
            }
            await websocket.send(json.dumps(subscribe_message))
            print(f"✅ 已订阅管道进度: {pipeline_id}")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    if data.get('type') == 'pipeline_progress':
                        progress = data.get('overall_progress', 0)
                        stage = data.get('current_stage', 'unknown')
                        print(f"  📊 进度: {progress:.1f}% - {stage}")
                        
                        if data.get('completed'):
                            print(f"  ✅ 分析完成!")
                            return data
                            
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"  ❌ WebSocket错误: {e}")
                    break
            
            return {"completed": False, "error": "timeout"}
            
    except Exception as e:
        print(f"  ❌ WebSocket连接失败: {e}")
        return {"completed": False, "error": str(e)}

async def test_deep_analysis():
    """测试深度分析功能"""
    print("🧠 测试深度分析功能修复")
    print("=" * 50)
    print(f"文档ID: {DOCUMENT_ID}")
    
    async with aiohttp.ClientSession() as session:
        # 1. 首先检查文档状态
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
                
                # 3. 监控进度
                if pipeline_id:
                    print("\n3️⃣ 监控分析进度...")
                    progress = await monitor_progress_with_websocket(pipeline_id, timeout=300)
                    
                    if progress.get('completed'):
                        duration = time.time() - start_time
                        print(f"\n⏱️  总耗时: {duration:.2f}秒")
                        
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
                                    
                                    if result.get('key_insights'):
                                        print(f"\n💡 关键洞察:")
                                        for i, insight in enumerate(result['key_insights'][:3], 1):
                                            print(f"  {i}. {insight}")
                                    
                                    print(f"\n✅ 深度分析功能已修复并正常工作!")
                                else:
                                    print(f"  ⚠️  分析结果为空")
                            else:
                                error_text = await analysis_resp.text()
                                print(f"  ❌ 获取分析结果失败: {analysis_resp.status}")
                                print(f"  错误: {error_text}")
                    else:
                        print(f"\n❌ 分析超时或失败")
            else:
                error_text = await resp.text()
                print(f"  ❌ 启动分析失败: {resp.status}")
                print(f"  错误: {error_text}")

async def main():
    await test_deep_analysis()

if __name__ == "__main__":
    print("🚀 启动深度分析功能测试...")
    print(f"API服务器: {API_BASE}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    asyncio.run(main())