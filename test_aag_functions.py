#!/usr/bin/env python3
"""
AAG页面核心功能测试脚本
测试四个核心功能：文档上传、文档摘要、文档索引、深度分析
"""

import asyncio
import aiohttp
import time
import json
import os
from pathlib import Path
from datetime import datetime
import websockets

# 配置
API_BASE = "http://localhost:8200"
WS_BASE = "ws://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"
USER_ID = "243588ff-459d-45b8-b77b-09aec3946a64"

# 测试文档内容
TEST_DOCUMENTS = {
    "test_upload.md": """# AI技术在医疗领域的应用研究

## 摘要
本文档探讨了人工智能技术在医疗诊断、药物研发和患者护理中的创新应用。通过机器学习和深度学习算法，AI正在revolutionize医疗行业。

## 主要内容
1. **医疗影像诊断**: 使用CNN进行X光、CT扫描分析
2. **精准医疗**: 基于基因组数据的个性化治疗方案
3. **药物发现**: AI加速新药研发流程
4. **智能问诊**: 自然语言处理技术辅助初步诊断

## 结论
AI技术正在显著提升医疗服务的质量和效率，但仍需要解决数据隐私、算法可解释性等挑战。

## 参考文献
[1] Smith et al., "AI in Healthcare", Nature Medicine, 2023
[2] Zhang et al., "Deep Learning for Medical Imaging", IEEE TMI, 2023
""",
    
    "test_chinese.md": """# 中文文档处理测试

## 引言
这是一个用于测试中文文档处理能力的示例文档。系统需要正确处理中文分词、句子边界识别等功能。

## 技术要点
1. **中文分词技术**：基于统计模型的分词算法
2. **句子边界检测**：处理中文标点符号，。！？等
3. **混合语言处理**：支持中英文mixed content的处理
4. **编码兼容性**：确保UTF-8编码的正确处理

## 测试场景
- 长句子处理：中文的句子结构与英文不同，往往包含多个子句，需要智能识别句子边界，避免在不恰当的位置进行分割。
- 专业术语：包含技术术语如API、WebSocket、LLM等英文缩写。
- 数字和符号：测试数字123、特殊符号@#$%的处理。

## 预期结果
系统应当能够准确识别中文内容，生成高质量的摘要，并创建有效的向量索引。
""",
    
    "test_large.md": """# 大文档处理性能测试

""" + ("这是一个用于测试大文档处理性能的段落。" * 100) + """

## 多章节内容测试

### 第一章：背景介绍
""" + ("详细的背景信息和研究动机说明。" * 50) + """

### 第二章：技术方案
""" + ("具体的技术实现方案和架构设计。" * 50) + """

### 第三章：实验结果
""" + ("实验设置、结果分析和性能评估。" * 50) + """

### 第四章：总结展望
""" + ("研究总结和未来工作展望。" * 50)
}

class AAGFunctionTester:
    def __init__(self):
        self.results = {
            "upload": [],
            "summary": [],
            "index": [],
            "analysis": []
        }
        self.uploaded_documents = []

    async def test_all(self):
        """运行所有测试"""
        print("🧪 开始AAG核心功能测试")
        print("=" * 60)
        
        # 1. 测试文档上传
        await self.test_document_upload()
        
        # 2. 测试文档摘要
        await self.test_document_summary()
        
        # 3. 测试文档索引
        await self.test_document_index()
        
        # 4. 测试深度分析
        await self.test_deep_analysis()
        
        # 5. 生成测试报告
        self.generate_report()

    async def test_document_upload(self):
        """测试文档上传功能"""
        print("\n📤 测试1: 文档上传功能")
        print("-" * 40)
        
        async with aiohttp.ClientSession() as session:
            for filename, content in TEST_DOCUMENTS.items():
                start_time = time.time()
                
                # 创建FormData
                data = aiohttp.FormData()
                data.add_field('file',
                             content.encode('utf-8'),
                             filename=filename,
                             content_type='text/plain')
                
                # 测试不同的处理选项
                test_cases = [
                    {"name": "仅上传", "params": "upload_only=true"},
                    {"name": "上传+摘要", "params": "upload_only=false&generate_summary=true"},
                    {"name": "上传+索引", "params": "upload_only=false&create_index=true"},
                    {"name": "上传+分析", "params": "upload_only=false&deep_analysis=true"}
                ]
                
                for test_case in test_cases[:1]:  # 先测试第一种情况
                    try:
                        print(f"\n测试文档: {filename} - {test_case['name']}")
                        
                        url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}&{test_case['params']}"
                        
                        async with session.post(url, data=data, headers=HEADERS) as resp:
                            duration = time.time() - start_time
                            
                            if resp.status == 200:
                                result = await resp.json()
                                self.uploaded_documents.append(result['document_id'])
                                
                                self.results["upload"].append({
                                    "filename": filename,
                                    "test_case": test_case['name'],
                                    "status": "✅ 成功",
                                    "duration": f"{duration:.2f}秒",
                                    "document_id": result['document_id'],
                                    "size": len(content.encode('utf-8'))
                                })
                                
                                print(f"  ✅ 上传成功")
                                print(f"  📄 文档ID: {result['document_id']}")
                                print(f"  ⏱️  耗时: {duration:.2f}秒")
                                print(f"  📊 大小: {len(content.encode('utf-8'))} bytes")
                                
                            else:
                                error_text = await resp.text()
                                self.results["upload"].append({
                                    "filename": filename,
                                    "test_case": test_case['name'],
                                    "status": "❌ 失败",
                                    "error": error_text,
                                    "duration": f"{duration:.2f}秒"
                                })
                                print(f"  ❌ 上传失败: {resp.status}")
                                print(f"  错误: {error_text}")
                                
                    except Exception as e:
                        self.results["upload"].append({
                            "filename": filename,
                            "test_case": test_case['name'],
                            "status": "❌ 异常",
                            "error": str(e)
                        })
                        print(f"  ❌ 异常: {e}")
                    
                    # 重新创建FormData以供下次使用
                    data = aiohttp.FormData()
                    data.add_field('file',
                                 content.encode('utf-8'),
                                 filename=filename,
                                 content_type='text/plain')

    async def test_document_summary(self):
        """测试文档摘要功能"""
        print("\n\n📝 测试2: 文档摘要功能")
        print("-" * 40)
        
        if not self.uploaded_documents:
            print("❌ 没有可用的文档进行摘要测试")
            return
        
        async with aiohttp.ClientSession() as session:
            for doc_id in self.uploaded_documents[:2]:  # 测试前两个文档
                start_time = time.time()
                
                try:
                    print(f"\n测试文档ID: {doc_id}")
                    
                    # 1. 启动摘要生成
                    url = f"{API_BASE}/api/v1/documents/{doc_id}/operations/summary/execute"
                    async with session.post(url, headers=HEADERS) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            pipeline_id = result.get('pipeline_id')
                            print(f"  ✅ 摘要任务启动成功")
                            print(f"  🔧 Pipeline ID: {pipeline_id}")
                            
                            # 2. 监听WebSocket进度
                            if pipeline_id:
                                progress = await self.monitor_progress_with_websocket(pipeline_id, timeout=60)
                                
                                if progress.get('completed'):
                                    duration = time.time() - start_time
                                    
                                    # 3. 获取摘要结果
                                    summary_url = f"{API_BASE}/api/v1/documents/{doc_id}/summary"
                                    async with session.get(summary_url, headers=HEADERS) as summary_resp:
                                        if summary_resp.status == 200:
                                            summary_data = await summary_resp.json()
                                            
                                            self.results["summary"].append({
                                                "document_id": doc_id,
                                                "status": "✅ 成功",
                                                "duration": f"{duration:.2f}秒",
                                                "summary_length": len(summary_data['summary']),
                                                "summary_preview": summary_data['summary'][:100] + "..."
                                            })
                                            
                                            print(f"  ✅ 摘要生成成功")
                                            print(f"  ⏱️  总耗时: {duration:.2f}秒")
                                            print(f"  📏 摘要长度: {len(summary_data['summary'])}字")
                                            print(f"  📄 摘要预览: {summary_data['summary'][:50]}...")
                                        else:
                                            self.results["summary"].append({
                                                "document_id": doc_id,
                                                "status": "❌ 获取失败",
                                                "error": await summary_resp.text()
                                            })
                                else:
                                    self.results["summary"].append({
                                        "document_id": doc_id,
                                        "status": "❌ 超时",
                                        "error": "摘要生成超时"
                                    })
                                    print(f"  ❌ 摘要生成超时")
                        else:
                            error_text = await resp.text()
                            self.results["summary"].append({
                                "document_id": doc_id,
                                "status": "❌ 启动失败",
                                "error": error_text
                            })
                            print(f"  ❌ 启动失败: {error_text}")
                            
                except Exception as e:
                    self.results["summary"].append({
                        "document_id": doc_id,
                        "status": "❌ 异常",
                        "error": str(e)
                    })
                    print(f"  ❌ 异常: {e}")

    async def test_document_index(self):
        """测试文档索引功能"""
        print("\n\n🔍 测试3: 文档索引功能")
        print("-" * 40)
        
        if not self.uploaded_documents:
            print("❌ 没有可用的文档进行索引测试")
            return
        
        async with aiohttp.ClientSession() as session:
            for doc_id in self.uploaded_documents[:2]:  # 测试前两个文档
                start_time = time.time()
                
                try:
                    print(f"\n测试文档ID: {doc_id}")
                    
                    # 1. 启动索引创建
                    url = f"{API_BASE}/api/v1/documents/{doc_id}/operations/index/execute"
                    async with session.post(url, headers=HEADERS) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            pipeline_id = result.get('pipeline_id')
                            print(f"  ✅ 索引任务启动成功")
                            print(f"  🔧 Pipeline ID: {pipeline_id}")
                            
                            # 2. 监听进度
                            if pipeline_id:
                                progress = await self.monitor_progress_with_websocket(pipeline_id, timeout=180)
                                
                                if progress.get('completed'):
                                    duration = time.time() - start_time
                                    
                                    # 3. 检查索引状态
                                    status_url = f"{API_BASE}/api/v1/documents/{doc_id}/operations/status"
                                    async with session.get(status_url, headers=HEADERS) as status_resp:
                                        if status_resp.status == 200:
                                            status_data = await status_resp.json()
                                            index_completed = status_data['operations_summary']['index_completed']
                                            
                                            self.results["index"].append({
                                                "document_id": doc_id,
                                                "status": "✅ 成功" if index_completed else "❌ 失败",
                                                "duration": f"{duration:.2f}秒",
                                                "index_completed": index_completed
                                            })
                                            
                                            print(f"  ✅ 索引创建{'成功' if index_completed else '失败'}")
                                            print(f"  ⏱️  总耗时: {duration:.2f}秒")
                                        else:
                                            self.results["index"].append({
                                                "document_id": doc_id,
                                                "status": "❌ 状态查询失败",
                                                "error": await status_resp.text()
                                            })
                                else:
                                    self.results["index"].append({
                                        "document_id": doc_id,
                                        "status": "❌ 超时",
                                        "error": "索引创建超时"
                                    })
                                    print(f"  ❌ 索引创建超时")
                        else:
                            error_text = await resp.text()
                            self.results["index"].append({
                                "document_id": doc_id,
                                "status": "❌ 启动失败",
                                "error": error_text
                            })
                            print(f"  ❌ 启动失败: {error_text}")
                            
                except Exception as e:
                    self.results["index"].append({
                        "document_id": doc_id,
                        "status": "❌ 异常",
                        "error": str(e)
                    })
                    print(f"  ❌ 异常: {e}")

    async def test_deep_analysis(self):
        """测试深度分析功能"""
        print("\n\n🧠 测试4: 深度分析功能")
        print("-" * 40)
        
        if not self.uploaded_documents:
            print("❌ 没有可用的文档进行分析测试")
            return
        
        async with aiohttp.ClientSession() as session:
            # 只测试第一个文档，因为深度分析耗时较长
            doc_id = self.uploaded_documents[0]
            start_time = time.time()
            
            try:
                print(f"\n测试文档ID: {doc_id}")
                
                # 1. 启动深度分析
                url = f"{API_BASE}/api/v1/documents/{doc_id}/operations/analysis/execute"
                async with session.post(url, headers=HEADERS) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        pipeline_id = result.get('pipeline_id')
                        print(f"  ✅ 分析任务启动成功")
                        print(f"  🔧 Pipeline ID: {pipeline_id}")
                        
                        # 2. 监听进度（深度分析需要更长时间）
                        if pipeline_id:
                            progress = await self.monitor_progress_with_websocket(pipeline_id, timeout=600)
                            
                            if progress.get('completed'):
                                duration = time.time() - start_time
                                
                                # 3. 获取分析结果
                                analysis_url = f"{API_BASE}/api/v1/documents/{doc_id}/analysis"
                                async with session.get(analysis_url, headers=HEADERS) as analysis_resp:
                                    if analysis_resp.status == 200:
                                        analysis_data = await analysis_resp.json()
                                        
                                        self.results["analysis"].append({
                                            "document_id": doc_id,
                                            "status": "✅ 成功",
                                            "duration": f"{duration:.2f}秒",
                                            "analysis_depth": analysis_data.get('analysis_depth', 'unknown'),
                                            "insights_count": len(analysis_data.get('result', {}).get('key_insights', [])),
                                            "action_items_count": len(analysis_data.get('result', {}).get('action_items', []))
                                        })
                                        
                                        print(f"  ✅ 深度分析成功")
                                        print(f"  ⏱️  总耗时: {duration:.2f}秒")
                                        print(f"  🔍 分析深度: {analysis_data.get('analysis_depth', 'unknown')}")
                                        print(f"  💡 洞察数量: {len(analysis_data.get('result', {}).get('key_insights', []))}")
                                        print(f"  🎯 行动项数: {len(analysis_data.get('result', {}).get('action_items', []))}")
                                    else:
                                        self.results["analysis"].append({
                                            "document_id": doc_id,
                                            "status": "❌ 获取失败",
                                            "error": await analysis_resp.text()
                                        })
                            else:
                                self.results["analysis"].append({
                                    "document_id": doc_id,
                                    "status": "❌ 超时",
                                    "error": "深度分析超时"
                                })
                                print(f"  ❌ 深度分析超时")
                    else:
                        error_text = await resp.text()
                        self.results["analysis"].append({
                            "document_id": doc_id,
                            "status": "❌ 启动失败",
                            "error": error_text
                        })
                        print(f"  ❌ 启动失败: {error_text}")
                        
            except Exception as e:
                self.results["analysis"].append({
                    "document_id": doc_id,
                    "status": "❌ 异常",
                    "error": str(e)
                })
                print(f"  ❌ 异常: {e}")

    async def monitor_progress_with_websocket(self, pipeline_id: str, timeout: int = 60):
        """通过WebSocket监控处理进度"""
        ws_url = f"{WS_BASE}/api/v1/ws/{USER_ID}?connection_id=test_{int(time.time())}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                # 订阅管道进度
                subscribe_message = {
                    "type": "subscribe_pipeline",
                    "pipeline_id": pipeline_id
                }
                await websocket.send(json.dumps(subscribe_message))
                
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(message)
                        
                        if data.get('type') == 'pipeline_progress':
                            print(f"    进度: {data.get('overall_progress', 0):.1f}% - {data.get('current_stage', 'unknown')}")
                            
                            if data.get('completed'):
                                return data
                                
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"    WebSocket错误: {e}")
                        break
                
                return {"completed": False, "error": "timeout"}
                
        except Exception as e:
            print(f"    WebSocket连接失败: {e}")
            return {"completed": False, "error": str(e)}

    def generate_report(self):
        """生成测试报告"""
        print("\n\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        # 统计结果
        for func_name, results in self.results.items():
            if results:
                print(f"\n### {func_name.upper()} 功能测试结果")
                success_count = sum(1 for r in results if "✅" in r.get("status", ""))
                total_count = len(results)
                success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                
                print(f"成功率: {success_rate:.1f}% ({success_count}/{total_count})")
                
                # 详细结果
                for result in results:
                    status = result.get("status", "unknown")
                    if "✅" in status:
                        if func_name == "upload":
                            print(f"  {status} {result.get('filename')} - {result.get('duration')}")
                        else:
                            print(f"  {status} {result.get('document_id', 'unknown')[:8]}... - {result.get('duration', 'N/A')}")
                    else:
                        error = result.get("error", "unknown error")
                        if len(error) > 50:
                            error = error[:50] + "..."
                        print(f"  {status} - {error}")
        
        # 保存详细报告
        report_path = Path("aag_test_results.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "test_time": datetime.now().isoformat(),
                "results": self.results,
                "uploaded_documents": self.uploaded_documents
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细测试结果已保存到: {report_path}")

async def main():
    tester = AAGFunctionTester()
    await tester.test_all()

if __name__ == "__main__":
    print("🚀 启动AAG功能测试...")
    print(f"API服务器: {API_BASE}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    asyncio.run(main())