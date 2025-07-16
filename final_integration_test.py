#!/usr/bin/env python3
"""
最终集成测试脚本
"""

import asyncio
import aiohttp
import time
import json
from pathlib import Path
from typing import Dict, Any, List

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"

class IntegrationTest:
    """集成测试类"""
    
    def __init__(self):
        self.results = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration": round(duration, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message} ({duration:.2f}s)")
    
    async def test_api_health(self):
        """测试API健康状态"""
        start_time = time.time()
        try:
            async with self.session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    health = await resp.json()
                    status = health.get('status', 'unknown')
                    self.log_result("API健康检查", True, f"状态: {status}", time.time() - start_time)
                    return True
                else:
                    self.log_result("API健康检查", False, f"状态码: {resp.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_result("API健康检查", False, f"异常: {e}", time.time() - start_time)
            return False
    
    async def test_project_list(self):
        """测试项目列表"""
        start_time = time.time()
        try:
            async with self.session.get(f"{API_BASE}/api/v1/projects", headers=HEADERS) as resp:
                if resp.status == 200:
                    projects = await resp.json()
                    count = len(projects)
                    self.log_result("项目列表", True, f"找到 {count} 个项目", time.time() - start_time)
                    return True
                else:
                    self.log_result("项目列表", False, f"状态码: {resp.status}", time.time() - start_time)
                    return False
        except Exception as e:
            self.log_result("项目列表", False, f"异常: {e}", time.time() - start_time)
            return False
    
    async def test_document_upload_only(self):
        """测试仅上传文档"""
        start_time = time.time()
        test_content = f"# 仅上传测试文档\n\n这是一个测试文档，时间戳: {time.time()}"
        test_file = Path(f"upload_only_test_{int(time.time())}.md")
        
        try:
            test_file.write_text(test_content)
            
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file.name)
                data.add_field('upload_only', 'true')
                
                upload_url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}"
                async with self.session.post(upload_url, data=data, headers=HEADERS) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        doc_id = result['document_id']
                        self.log_result("仅上传文档", True, f"文档ID: {doc_id[:8]}...", time.time() - start_time)
                        return True, doc_id
                    else:
                        error = await resp.text()
                        self.log_result("仅上传文档", False, f"状态码: {resp.status}", time.time() - start_time)
                        return False, None
        except Exception as e:
            self.log_result("仅上传文档", False, f"异常: {e}", time.time() - start_time)
            return False, None
        finally:
            if test_file.exists():
                test_file.unlink()
    
    async def test_document_with_processing(self):
        """测试带处理的文档上传"""
        start_time = time.time()
        test_content = f"""# 处理测试文档

## 概述
这是一个用于测试文档处理流程的测试文档。

## 内容
- 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 测试目标: 验证摘要生成和索引创建
- 预期结果: 系统应在合理时间内完成处理

## 技术细节
文档处理包括以下步骤：
1. 文档上传
2. 文本提取
3. 摘要生成
4. 向量化处理
5. 索引创建

## 结论
这个测试用于验证整个处理管道的稳定性。
"""
        
        test_file = Path(f"processing_test_{int(time.time())}.md")
        
        try:
            test_file.write_text(test_content)
            
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file.name)
                data.add_field('upload_only', 'false')
                data.add_field('generate_summary', 'true')
                data.add_field('create_index', 'true')
                data.add_field('deep_analysis', 'false')
                
                upload_url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}"
                async with self.session.post(upload_url, data=data, headers=HEADERS) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        doc_id = result['document_id']
                        pipeline_data = result.get('processing_pipeline')
                        
                        if pipeline_data:
                            pipeline_id = pipeline_data['pipeline_id']
                            
                            # 监控处理进度
                            success = await self._monitor_pipeline(pipeline_id, doc_id)
                            
                            duration = time.time() - start_time
                            if success:
                                self.log_result("文档处理", True, f"处理完成", duration)
                                return True, doc_id
                            else:
                                self.log_result("文档处理", False, f"处理失败或超时", duration)
                                return False, None
                        else:
                            self.log_result("文档处理", False, "未创建处理管道", time.time() - start_time)
                            return False, None
                    else:
                        error = await resp.text()
                        self.log_result("文档处理", False, f"上传失败: {resp.status}", time.time() - start_time)
                        return False, None
                        
        except Exception as e:
            self.log_result("文档处理", False, f"异常: {e}", time.time() - start_time)
            return False, None
        finally:
            if test_file.exists():
                test_file.unlink()
    
    async def _monitor_pipeline(self, pipeline_id: str, doc_id: str, timeout: int = 180):
        """监控管道处理进度"""
        for i in range(timeout // 5):
            await asyncio.sleep(5)
            
            try:
                status_url = f"{API_BASE}/api/v1/pipelines/{pipeline_id}/status"
                async with self.session.get(status_url, headers=HEADERS) as resp:
                    if resp.status == 200:
                        status = await resp.json()
                        progress = status.get('overall_progress', 0)
                        
                        if status.get('completed'):
                            return True
                        elif status.get('interrupted'):
                            return False
                        
                        # 打印进度（每30秒）
                        if i % 6 == 0:
                            current_stage = status.get('current_stage', 'unknown')
                            print(f"    进度: {progress:.1f}% - {current_stage}")
                    else:
                        print(f"    状态查询失败: {resp.status}")
                        return False
            except Exception as e:
                print(f"    监控异常: {e}")
                return False
        
        print(f"    处理超时 ({timeout}秒)")
        return False
    
    async def test_qa_functionality(self, doc_id: str):
        """测试问答功能"""
        start_time = time.time()
        
        questions = [
            "这个文档的主要内容是什么？",
            "文档中提到了哪些技术细节？",
            "测试的目标是什么？"
        ]
        
        success_count = 0
        for question in questions:
            try:
                qa_data = {
                    "question": question,
                    "project_id": PROJECT_ID
                }
                
                qa_url = f"{API_BASE}/api/v1/qa/answer"
                async with self.session.post(qa_url, json=qa_data, headers=HEADERS) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        answer = result.get('answer', '')
                        sources = result.get('sources', [])
                        
                        if answer and len(answer) > 10:
                            success_count += 1
                            print(f"    Q: {question}")
                            print(f"    A: {answer[:100]}...")
                            print(f"    来源: {len(sources)} 个")
                        else:
                            print(f"    问答失败: 答案为空或过短")
                    else:
                        print(f"    问答失败: {resp.status}")
                        
            except Exception as e:
                print(f"    问答异常: {e}")
        
        success_rate = success_count / len(questions)
        duration = time.time() - start_time
        
        if success_rate >= 0.6:  # 60%成功率
            self.log_result("问答功能", True, f"成功率: {success_rate:.1%}", duration)
            return True
        else:
            self.log_result("问答功能", False, f"成功率: {success_rate:.1%}", duration)
            return False
    
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        start_time = time.time()
        
        try:
            import websockets
            
            ws_url = f"ws://localhost:8200/api/v1/ws/243588ff-459d-45b8-b77b-09aec3946a64?connection_id=test_connection"
            
            async with websockets.connect(ws_url) as websocket:
                # 发送测试消息
                test_message = {"type": "test", "data": "hello"}
                await websocket.send(json.dumps(test_message))
                
                # 等待响应（超时3秒）
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    self.log_result("WebSocket连接", True, "连接成功", time.time() - start_time)
                    return True
                except asyncio.TimeoutError:
                    self.log_result("WebSocket连接", True, "连接成功（无响应）", time.time() - start_time)
                    return True
                    
        except Exception as e:
            self.log_result("WebSocket连接", False, f"异常: {e}", time.time() - start_time)
            return False
    
    def generate_report(self):
        """生成测试报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        report = f"""
# DPA系统最终集成测试报告

## 测试概览
- 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 总测试数: {total_tests}
- 通过: {passed_tests}
- 失败: {failed_tests}
- 成功率: {success_rate:.1%}

## 测试结果详情
"""
        
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            report += f"\n### {status} {result['test']}\n"
            report += f"- 状态: {'通过' if result['success'] else '失败'}\n"
            report += f"- 消息: {result['message']}\n"
            report += f"- 耗时: {result['duration']}秒\n"
            report += f"- 时间: {result['timestamp']}\n"
        
        # 评估系统状态
        if success_rate >= 0.8:
            status = "🟢 优秀"
        elif success_rate >= 0.6:
            status = "🟡 良好"
        else:
            status = "🔴 需要改进"
        
        report += f"""
## 系统状态评估
{status} (成功率: {success_rate:.1%})

## 建议
"""
        
        if success_rate >= 0.8:
            report += "- 系统运行良好，可以投入生产使用\n"
        elif success_rate >= 0.6:
            report += "- 系统基本稳定，建议修复失败的测试项\n"
        else:
            report += "- 系统存在较多问题，需要进一步调试和修复\n"
        
        return report

async def main():
    """主函数"""
    print("🚀 开始DPA系统最终集成测试")
    print("=" * 60)
    
    async with IntegrationTest() as test:
        # 基础功能测试
        print("\n📋 基础功能测试")
        await test.test_api_health()
        await test.test_project_list()
        await test.test_websocket_connection()
        
        # 文档管理测试
        print("\n📄 文档管理测试")
        success, doc_id = await test.test_document_upload_only()
        
        # 文档处理测试
        print("\n⚙️  文档处理测试")
        success, processed_doc_id = await test.test_document_with_processing()
        
        # 问答功能测试
        if success and processed_doc_id:
            print("\n💬 问答功能测试")
            await test.test_qa_functionality(processed_doc_id)
        
        # 生成报告
        print("\n📊 生成测试报告...")
        report = test.generate_report()
        
        # 保存报告
        report_file = Path("FINAL_INTEGRATION_TEST_REPORT.md")
        report_file.write_text(report)
        
        print(f"\n✅ 测试完成!")
        print(f"📄 报告文件: {report_file}")
        
        # 显示摘要
        total = len(test.results)
        passed = sum(1 for r in test.results if r['success'])
        success_rate = passed / total if total > 0 else 0
        
        print(f"\n📊 测试摘要: {passed}/{total} 通过 ({success_rate:.1%})")
        
        if success_rate >= 0.8:
            print("🎉 系统运行良好!")
        elif success_rate >= 0.6:
            print("⚠️  系统基本稳定，有改进空间")
        else:
            print("❌ 系统需要进一步修复")

if __name__ == "__main__":
    asyncio.run(main())