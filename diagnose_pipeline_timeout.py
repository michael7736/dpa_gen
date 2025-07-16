#!/usr/bin/env python3
"""
诊断处理管道超时问题
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path
import threading
import multiprocessing

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"

async def diagnose_pipeline_timeout():
    """诊断管道超时问题"""
    print("🔍 诊断处理管道超时问题")
    print("=" * 60)
    
    # 1. 系统环境检查
    print("\n1️⃣ 系统环境检查")
    print(f"   Python进程数: {len(list(filter(lambda p: 'python' in p, [str(p) for p in multiprocessing.active_children()])))} 个")
    print(f"   活跃线程数: {threading.active_count()} 个")
    
    # 2. 创建最小测试文档
    test_content = """# 最小测试文档
这是一个最小的测试文档，用于诊断处理管道问题。
内容很短，应该能快速处理。
"""
    
    test_file = Path(f"minimal_test_{int(time.time())}.md")
    test_file.write_text(test_content)
    
    print(f"\n2️⃣ 创建最小测试文档: {test_file}")
    print(f"   文档大小: {len(test_content)} 字符")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 3. 测试仅摘要生成
            print("\n3️⃣ 测试仅摘要生成（无索引和分析）")
            
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file.name)
                data.add_field('upload_only', 'false')
                data.add_field('generate_summary', 'true')
                data.add_field('create_index', 'false')
                data.add_field('deep_analysis', 'false')
                
                upload_start = time.time()
                upload_url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}"
                
                async with session.post(upload_url, data=data, headers=HEADERS) as resp:
                    upload_time = time.time() - upload_start
                    print(f"   上传响应时间: {upload_time:.2f}秒")
                    
                    if resp.status == 200:
                        result = await resp.json()
                        document_id = result['document_id']
                        pipeline_data = result.get('processing_pipeline')
                        
                        if pipeline_data:
                            pipeline_id = pipeline_data['pipeline_id']
                            print(f"   ✅ 管道创建成功: {pipeline_id}")
                            print(f"   📋 处理阶段: {len(pipeline_data.get('stages', []))} 个")
                            
                            # 4. 详细监控管道执行
                            print("\n4️⃣ 详细监控管道执行")
                            monitor_start = time.time()
                            last_progress = -1
                            stalled_count = 0
                            
                            for i in range(60):  # 5分钟超时
                                await asyncio.sleep(5)
                                
                                try:
                                    status_url = f"{API_BASE}/api/v1/pipelines/{pipeline_id}/status"
                                    async with session.get(status_url, headers=HEADERS) as status_resp:
                                        if status_resp.status == 200:
                                            status = await status_resp.json()
                                            progress = status.get('overall_progress', 0)
                                            current_stage = status.get('current_stage', 'unknown')
                                            completed = status.get('completed', False)
                                            
                                            # 检查是否停滞
                                            if progress == last_progress:
                                                stalled_count += 1
                                            else:
                                                stalled_count = 0
                                            last_progress = progress
                                            
                                            elapsed = time.time() - monitor_start
                                            print(f"   [{elapsed:5.1f}s] 进度: {progress:5.1f}% | 阶段: {current_stage} | 停滞: {stalled_count}次")
                                            
                                            # 显示详细阶段信息
                                            if status.get('stages'):
                                                for stage in status['stages']:
                                                    stage_type = stage['stage_type']
                                                    stage_status = stage['status']
                                                    stage_progress = stage['progress']
                                                    stage_message = stage.get('message', '')
                                                    
                                                    print(f"     └─ {stage_type}: {stage_status} ({stage_progress}%) - {stage_message}")
                                                    
                                                    if stage.get('error'):
                                                        print(f"        ❌ 错误: {stage['error']}")
                                            
                                            # 检查完成状态
                                            if completed:
                                                total_time = time.time() - monitor_start
                                                print(f"\n   ✅ 处理完成! 总耗时: {total_time:.2f}秒")
                                                break
                                            
                                            # 检查是否停滞过久
                                            if stalled_count >= 6:  # 30秒无进展
                                                print(f"\n   ⚠️  处理停滞 {stalled_count * 5}秒，可能存在问题")
                                        else:
                                            print(f"   ❌ 获取状态失败: {status_resp.status}")
                                            
                                except Exception as e:
                                    print(f"   ❌ 监控异常: {e}")
                            
                            else:
                                print(f"\n   ❌ 处理超时（5分钟）")
                                
                                # 5. 检查系统资源
                                print("\n5️⃣ 检查系统资源")
                                try:
                                    # 检查数据库连接
                                    health_url = f"{API_BASE}/health"
                                    async with session.get(health_url) as health_resp:
                                        if health_resp.status == 200:
                                            health_data = await health_resp.json()
                                            print(f"   API健康状态: {health_data['status']}")
                                            if 'database' in health_data:
                                                print(f"   数据库状态: {health_data['database']}")
                                        else:
                                            print(f"   API健康检查失败: {health_resp.status}")
                                except Exception as e:
                                    print(f"   健康检查异常: {e}")
                        else:
                            print("   ❌ 未创建处理管道")
                    else:
                        error_text = await resp.text()
                        print(f"   ❌ 上传失败: {resp.status}")
                        print(f"   错误详情: {error_text}")
                        
        except Exception as e:
            print(f"❌ 诊断异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
                print(f"\n🧹 已清理测试文件: {test_file}")

async def main():
    print("🚀 启动管道超时诊断")
    print(f"目标API: {API_BASE}")
    print(f"项目ID: {PROJECT_ID}")
    await diagnose_pipeline_timeout()

if __name__ == "__main__":
    asyncio.run(main())