#!/usr/bin/env python3
"""
验证管道修复效果
"""

import asyncio
import aiohttp
import time
from pathlib import Path

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"

async def verify_pipeline_fix():
    """验证管道修复效果"""
    print("🧪 验证管道修复效果")
    print("=" * 50)
    
    # 创建测试文档
    test_content = f"""# 管道测试文档 - {time.strftime('%Y-%m-%d %H:%M:%S')}

## 测试目标
验证处理管道的稳定性和错误处理能力。

## 测试内容
- 摘要生成测试
- 超时控制测试
- 错误处理测试
- WebSocket通知测试

## 技术要点
1. **后台任务执行**: 使用asyncio.wait_for进行超时控制
2. **异常处理**: 捕获并记录所有异常
3. **状态管理**: 正确标记管道状态
4. **通知机制**: WebSocket实时通知

## 预期结果
系统应能在合理时间内完成处理，或在超时时正确处理。
"""
    
    test_file = Path(f"pipeline_test_{int(time.time())}.md")
    test_file.write_text(test_content)
    
    print(f"📄 测试文件: {test_file}")
    print(f"📊 文档大小: {len(test_content)} 字符")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 健康检查
            print("\n1️⃣ 健康检查...")
            async with session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    health = await resp.json()
                    print(f"   API状态: {health['status']}")
                else:
                    print(f"   ❌ API不健康: {resp.status}")
                    return False
            
            # 2. 上传并启动处理
            print("\n2️⃣ 上传并启动处理...")
            
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
                    
                    if resp.status == 200:
                        result = await resp.json()
                        document_id = result['document_id']
                        pipeline_data = result.get('processing_pipeline')
                        
                        print(f"   ✅ 上传成功 ({upload_time:.2f}s)")
                        print(f"   📄 文档ID: {document_id}")
                        print(f"   📋 消息: {result['message']}")
                        
                        if pipeline_data:
                            pipeline_id = pipeline_data['pipeline_id']
                            stages = pipeline_data.get('stages', [])
                            print(f"   🔧 管道ID: {pipeline_id}")
                            print(f"   📊 处理阶段: {len(stages)} 个")
                            
                            # 3. 详细监控处理过程
                            print("\n3️⃣ 监控处理过程...")
                            
                            monitor_start = time.time()
                            last_progress = -1
                            stall_count = 0
                            
                            for i in range(120):  # 10分钟监控
                                await asyncio.sleep(5)
                                
                                status_url = f"{API_BASE}/api/v1/pipelines/{pipeline_id}/status"
                                async with session.get(status_url, headers=HEADERS) as status_resp:
                                    if status_resp.status == 200:
                                        status = await status_resp.json()
                                        progress = status.get('overall_progress', 0)
                                        current_stage = status.get('current_stage', 'unknown')
                                        completed = status.get('completed', False)
                                        interrupted = status.get('interrupted', False)
                                        
                                        # 检查停滞
                                        if progress == last_progress:
                                            stall_count += 1
                                        else:
                                            stall_count = 0
                                        last_progress = progress
                                        
                                        elapsed = time.time() - monitor_start
                                        print(f"   [{elapsed:5.1f}s] 进度: {progress:5.1f}% | 阶段: {current_stage} | 停滞: {stall_count}次")
                                        
                                        # 显示阶段详情
                                        if status.get('stages'):
                                            for stage in status['stages']:
                                                stage_type = stage['stage_type']
                                                stage_status = stage['status']
                                                stage_progress = stage.get('progress', 0)
                                                stage_message = stage.get('message', '')
                                                
                                                if stage_status == 'PROCESSING':
                                                    print(f"     ⚙️  {stage_type}: {stage_progress}% - {stage_message}")
                                                elif stage_status == 'COMPLETED':
                                                    print(f"     ✅ {stage_type}: 完成")
                                                elif stage_status == 'FAILED':
                                                    print(f"     ❌ {stage_type}: 失败 - {stage.get('error', '未知错误')}")
                                        
                                        # 检查完成状态
                                        if completed:
                                            total_time = time.time() - monitor_start
                                            print(f"\n   ✅ 处理完成! 总耗时: {total_time:.2f}秒")
                                            
                                            # 获取处理结果
                                            print("\n4️⃣ 获取处理结果...")
                                            
                                            # 获取摘要
                                            summary_url = f"{API_BASE}/api/v1/documents/{document_id}/summary"
                                            async with session.get(summary_url, headers=HEADERS) as summary_resp:
                                                if summary_resp.status == 200:
                                                    summary_data = await summary_resp.json()
                                                    print(f"   📝 摘要长度: {len(summary_data['summary'])} 字符")
                                                    print(f"   🔑 关键词: {', '.join(summary_data['keywords'][:5])}")
                                                    print(f"   📖 摘要预览: {summary_data['summary'][:150]}...")
                                                else:
                                                    print(f"   ❌ 获取摘要失败: {summary_resp.status}")
                                            
                                            return True
                                            
                                        # 检查中断状态
                                        if interrupted:
                                            print(f"\n   ⚠️  处理被中断")
                                            return False
                                        
                                        # 检查长时间停滞
                                        if stall_count >= 12:  # 1分钟无进展
                                            print(f"\n   ⚠️  处理停滞超过1分钟，可能存在问题")
                                    else:
                                        print(f"   ❌ 状态查询失败: {status_resp.status}")
                                        break
                            
                            print(f"\n   ❌ 监控超时（10分钟）")
                            return False
                            
                        else:
                            print(f"   ⚠️  没有创建处理管道")
                            return False
                    else:
                        error_text = await resp.text()
                        print(f"   ❌ 上传失败: {resp.status}")
                        print(f"   错误: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ 验证异常: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
                print(f"\n🧹 已清理测试文件: {test_file}")

async def main():
    """主函数"""
    print("🚀 启动管道修复验证")
    print(f"API服务器: {API_BASE}")
    print(f"项目ID: {PROJECT_ID}")
    
    success = await verify_pipeline_fix()
    
    if success:
        print("\n🎉 验证成功! 管道修复有效")
    else:
        print("\n💥 验证失败! 需要进一步调试")
        
    return success

if __name__ == "__main__":
    asyncio.run(main())