#!/usr/bin/env python3
"""
测试WebSocket + V2文档处理系统
"""

import asyncio
import websockets
import json
import aiohttp
import tempfile
import os
from pathlib import Path

# 测试配置
API_BASE = "http://localhost:8200"
WS_URL = "ws://localhost:8200/api/v1/ws/243588ff-459d-45b8-b77b-09aec3946a64"
USER_ID = "243588ff-459d-45b8-b77b-09aec3946a64"

async def test_websocket_connection():
    """测试WebSocket连接"""
    print("🔌 测试WebSocket连接...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket连接成功")
            
            # 测试ping
            await websocket.send(json.dumps({
                "type": "ping",
                "timestamp": 1234567890
            }))
            
            response = await websocket.recv()
            message = json.loads(response)
            print(f"📨 收到响应: {message['type']}")
            
            return True
            
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        return False

async def upload_test_document():
    """上传测试文档"""
    print("📄 创建并上传测试文档...")
    
    # 创建测试文档
    test_content = """# WebSocket测试文档

这是一个用于测试WebSocket实时进度推送的示例文档。

## 主要内容

1. **系统测试**: 验证V2文档处理系统
2. **实时通信**: 测试WebSocket连接和进度推送
3. **处理管道**: 测试摘要、索引、分析流程

## 技术特性

- MinIO对象存储
- 实时进度跟踪
- 中断恢复机制
- WebSocket通信

这个文档包含足够的内容来触发各种处理阶段，
确保我们能够测试完整的处理管道功能。
"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        # 准备上传数据
        data = aiohttp.FormData()
        data.add_field('upload_only', 'false')
        data.add_field('generate_summary', 'true')
        data.add_field('create_index', 'true')
        data.add_field('deep_analysis', 'false')
        
        # 添加文件
        with open(temp_file_path, 'rb') as f:
            data.add_field('file', f, filename='websocket_test.md', content_type='text/markdown')
            
            # 上传请求
            headers = {"X-USER-ID": USER_ID}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE}/api/v2/documents/upload",
                    data=data,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 文档上传成功")
                        print(f"   文档ID: {result['document_id']}")
                        print(f"   文件名: {result['filename']}")
                        
                        if 'processing_pipeline' in result:
                            pipeline_id = result['processing_pipeline']['pipeline_id']
                            print(f"   管道ID: {pipeline_id}")
                            return result['document_id'], pipeline_id
                        else:
                            print("   仅上传模式，无处理管道")
                            return result['document_id'], None
                    else:
                        error_text = await response.text()
                        print(f"❌ 上传失败: {response.status} - {error_text}")
                        return None, None
                        
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None, None
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file_path)
        except:
            pass

async def monitor_pipeline_progress(pipeline_id):
    """通过WebSocket监控管道进度"""
    print(f"📊 开始监控管道进度: {pipeline_id}")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("🔌 WebSocket连接建立")
            
            # 订阅管道进度
            await websocket.send(json.dumps({
                "type": "subscribe_pipeline",
                "pipeline_id": pipeline_id
            }))
            
            print("📡 已订阅管道进度更新")
            
            # 监听进度更新
            completed = False
            timeout_count = 0
            max_timeout = 60  # 60秒超时
            
            while not completed and timeout_count < max_timeout:
                try:
                    # 设置超时
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    print(f"📨 收到消息: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'pipeline_progress':
                        progress = data.get('overall_progress', 0)
                        current_stage = data.get('current_stage', 'unknown')
                        stages = data.get('stages', [])
                        
                        print(f"   总进度: {progress:.1f}%")
                        print(f"   当前阶段: {current_stage}")
                        
                        # 显示各阶段状态
                        for stage in stages:
                            status = stage.get('status', 'unknown')
                            stage_progress = stage.get('progress', 0)
                            stage_name = stage.get('name', stage.get('id', 'unnamed'))
                            message = stage.get('message', '')
                            
                            status_emoji = {
                                'pending': '⏳',
                                'processing': '🔄',
                                'completed': '✅',
                                'failed': '❌',
                                'interrupted': '⏸️'
                            }.get(status, '❓')
                            
                            print(f"     {status_emoji} {stage_name}: {stage_progress}% - {message}")
                        
                        # 检查是否完成
                        if data.get('completed') or progress >= 100:
                            print("🎉 处理完成!")
                            completed = True
                            
                    elif data.get('type') == 'stage_update':
                        stage_name = data.get('stage_name', 'unknown')
                        stage_progress = data.get('progress', 0)
                        stage_message = data.get('message', '')
                        print(f"   阶段更新 - {stage_name}: {stage_progress}% - {stage_message}")
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    if timeout_count % 10 == 0:  # 每10秒显示一次等待信息
                        print(f"⏱️  等待进度更新... ({timeout_count}s)")
                    continue
                except Exception as e:
                    print(f"❌ 接收消息异常: {e}")
                    break
            
            if timeout_count >= max_timeout:
                print("⏰ 监控超时")
            
            # 取消订阅
            await websocket.send(json.dumps({
                "type": "unsubscribe_pipeline",
                "pipeline_id": pipeline_id
            }))
            
            print("📡 已取消订阅")
            
    except Exception as e:
        print(f"❌ WebSocket监控异常: {e}")

async def test_complete_workflow():
    """测试完整工作流"""
    print("🚀 开始测试WebSocket + V2文档处理系统")
    print("=" * 50)
    
    # 1. 测试WebSocket连接
    ws_ok = await test_websocket_connection()
    if not ws_ok:
        print("❌ WebSocket连接测试失败，退出")
        return
    
    print()
    
    # 2. 上传测试文档
    doc_id, pipeline_id = await upload_test_document()
    if not doc_id:
        print("❌ 文档上传失败，退出")
        return
    
    print()
    
    # 3. 监控处理进度（如果有管道）
    if pipeline_id:
        await monitor_pipeline_progress(pipeline_id)
    else:
        print("ℹ️  仅上传模式，无需监控处理进度")
    
    print()
    print("🎯 测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())