#!/usr/bin/env python3
"""
简单的处理测试 - 不依赖shell环境
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path

async def test_processing():
    """测试处理功能"""
    print("🧪 测试处理功能")
    print("=" * 50)
    
    # 创建测试文件
    test_content = """# 测试文档
    
这是一个简单的测试文档，用于验证处理管道。

## 内容
- 测试摘要生成
- 测试索引创建
- 验证系统稳定性
"""
    
    test_file = Path(f"test_processing_{int(time.time())}.md")
    test_file.write_text(test_content)
    
    print(f"📄 创建测试文件: {test_file}")
    
    API_BASE = "http://localhost:8200"
    HEADERS = {"X-USER-ID": "u1"}
    PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 测试健康检查
            print("\n1️⃣ 健康检查...")
            async with session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    health = await resp.json()
                    print(f"   ✅ API状态: {health['status']}")
                else:
                    print(f"   ❌ API不健康: {resp.status}")
                    return
            
            # 2. 上传并开始处理
            print("\n2️⃣ 上传文档...")
            
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file.name)
                data.add_field('upload_only', 'false')
                data.add_field('generate_summary', 'true')
                data.add_field('create_index', 'false')  # 只测试摘要
                data.add_field('deep_analysis', 'false')
                
                upload_url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}"
                
                try:
                    async with session.post(upload_url, data=data, headers=HEADERS) as resp:
                        print(f"   响应状态: {resp.status}")
                        
                        if resp.status == 200:
                            result = await resp.json()
                            document_id = result['document_id']
                            
                            print(f"   ✅ 上传成功: {document_id}")
                            print(f"   消息: {result['message']}")
                            
                            # 检查是否有处理管道
                            pipeline_data = result.get('processing_pipeline')
                            if pipeline_data:
                                pipeline_id = pipeline_data['pipeline_id']
                                print(f"   📊 管道ID: {pipeline_id}")
                                
                                # 3. 监控处理进度
                                print("\n3️⃣ 监控处理进度...")
                                
                                for i in range(12):  # 1分钟超时
                                    await asyncio.sleep(5)
                                    
                                    try:
                                        status_url = f"{API_BASE}/api/v1/pipelines/{pipeline_id}/status"
                                        async with session.get(status_url, headers=HEADERS) as status_resp:
                                            if status_resp.status == 200:
                                                status = await status_resp.json()
                                                progress = status.get('overall_progress', 0)
                                                current_stage = status.get('current_stage', 'unknown')
                                                
                                                print(f"   [{i*5:2d}s] 进度: {progress:5.1f}% | 阶段: {current_stage}")
                                                
                                                if status.get('completed'):
                                                    print(f"   ✅ 处理完成!")
                                                    
                                                    # 获取摘要
                                                    summary_url = f"{API_BASE}/api/v1/documents/{document_id}/summary"
                                                    async with session.get(summary_url, headers=HEADERS) as summary_resp:
                                                        if summary_resp.status == 200:
                                                            summary_data = await summary_resp.json()
                                                            print(f"\n📝 摘要: {summary_data['summary'][:100]}...")
                                                            print(f"🔑 关键词: {', '.join(summary_data['keywords'][:3])}")
                                                    break
                                                    
                                                # 检查错误
                                                if status.get('stages'):
                                                    for stage in status['stages']:
                                                        if stage.get('error'):
                                                            print(f"   ❌ 阶段错误: {stage['error']}")
                                                            return
                                            else:
                                                print(f"   ❌ 状态查询失败: {status_resp.status}")
                                    except Exception as e:
                                        print(f"   ❌ 监控异常: {e}")
                                        break
                                else:
                                    print(f"   ❌ 处理超时（1分钟）")
                            else:
                                print(f"   ⚠️  没有处理管道数据")
                        else:
                            error_text = await resp.text()
                            print(f"   ❌ 上传失败: {resp.status}")
                            print(f"   错误: {error_text}")
                            
                except Exception as e:
                    print(f"   ❌ 上传异常: {e}")
                    
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # 清理
            if test_file.exists():
                test_file.unlink()
                print(f"\n🧹 已清理: {test_file}")

if __name__ == "__main__":
    asyncio.run(test_processing())