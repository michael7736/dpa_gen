#!/usr/bin/env python3
"""
测试WebSocket完成通知修复
"""

import asyncio
import json
import aiohttp
import websockets
from datetime import datetime

async def test_websocket_completion():
    """测试摘要生成完成后是否收到WebSocket通知"""
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始测试WebSocket完成通知修复...")
    
    # 1. 建立WebSocket连接
    ws_url = "ws://localhost:8200/api/v1/ws/243588ff-459d-45b8-b77b-09aec3946a64?connection_id=test123"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WebSocket连接已建立")
            
            # 监听WebSocket消息的任务
            messages_received = []
            
            async def listen_messages():
                try:
                    while True:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(message)
                        messages_received.append(data)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📨 收到WebSocket消息: {data.get('type', 'unknown')}")
                        
                        if data.get('type') == 'pipeline_progress' and data.get('completed'):
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 收到完成通知！")
                            return True
                except asyncio.TimeoutError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ WebSocket监听超时")
                    return False
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ WebSocket消息监听错误: {e}")
                    return False
            
            # 2. 启动摘要生成任务
            async with aiohttp.ClientSession() as session:
                # 使用新上传的测试文档
                document_id = "4e5cf860-e9c2-463a-972a-ed1c329d415b"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📄 使用测试文档 (ID: {document_id})")
                
                # 启动摘要生成
                async with session.post(
                    f"http://localhost:8200/api/v1/documents/{document_id}/operations/start",
                    headers={"X-USER-ID": "u1"},
                    json={
                        "generate_summary": True,
                        "create_index": False,
                        "deep_analysis": False
                    }
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ 启动摘要生成失败: {resp.status}")
                        response_text = await resp.text()
                        print(f"响应内容: {response_text}")
                        return False
                    
                    result = await resp.json()
                    pipeline_id = result.get("pipeline_id")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 摘要生成已启动，Pipeline ID: {pipeline_id}")
                
                # 订阅管道进度
                subscribe_message = {
                    "type": "subscribe_pipeline",
                    "pipeline_id": pipeline_id
                }
                await websocket.send(json.dumps(subscribe_message))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 已订阅管道进度")
                
                # 启动消息监听任务
                listen_task = asyncio.create_task(listen_messages())
                
                # 等待完成或超时
                try:
                    completed = await asyncio.wait_for(listen_task, timeout=60)
                    if completed:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 测试成功：收到了完成通知")
                        print(f"总共收到 {len(messages_received)} 条消息")
                        return True
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 测试失败：未收到完成通知")
                        return False
                except asyncio.TimeoutError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 测试超时：60秒内未收到完成通知")
                    return False
    
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket_completion())
    print(f"\n测试结果: {'通过' if result else '失败'}")