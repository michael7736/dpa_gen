#!/usr/bin/env python3
"""
测试完整的文档处理流程
包括：上传、摘要、索引、深度分析
"""

import asyncio
import aiohttp
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"

# 测试文档内容
import uuid
TEST_CONTENT = f"""# AI深度学习研究报告 - {uuid.uuid4()}

## 摘要
本报告深入探讨了深度学习在人工智能领域的最新进展，包括Transformer架构、大语言模型和多模态学习等关键技术。

## 1. 引言
深度学习作为人工智能的核心技术，在过去十年中取得了突破性进展。从AlexNet到GPT-4，深度学习模型的能力呈指数级增长。

## 2. 技术发展
### 2.1 Transformer架构
Transformer架构通过自注意力机制革新了序列建模，成为现代NLP的基础。

### 2.2 大语言模型
GPT系列、BERT等大语言模型展示了规模效应，参数量从数亿增长到千亿级别。

### 2.3 多模态学习
CLIP、DALL-E等模型实现了视觉和语言的融合，开启了多模态AI时代。

## 3. 应用场景
- 自然语言处理：机器翻译、文本生成、情感分析
- 计算机视觉：图像识别、目标检测、图像生成
- 语音识别：实时转录、语音合成
- 推荐系统：个性化推荐、用户行为预测

## 4. 挑战与机遇
### 4.1 计算资源需求
大模型训练需要大量GPU资源，成本高昂。

### 4.2 数据隐私
如何在保护隐私的同时训练有效模型是重要挑战。

### 4.3 可解释性
深度学习模型的黑箱特性限制了在某些领域的应用。

## 5. 未来展望
- 更高效的模型架构
- 少样本学习能力提升
- 人机协作的新模式
- 通用人工智能的探索

## 结论
深度学习技术正在快速发展，将继续推动AI革命，改变人类社会的方方面面。

## 参考文献
1. Vaswani et al. "Attention is All You Need" (2017)
2. Brown et al. "Language Models are Few-Shot Learners" (2020)
3. Radford et al. "Learning Transferable Visual Models From Natural Language Supervision" (2021)
"""

async def test_complete_flow():
    """测试完整流程"""
    print("🚀 开始完整流程测试")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 1. 创建测试文档
        test_file = Path("test_ai_report.md")
        test_file.write_text(TEST_CONTENT, encoding='utf-8')
        print(f"✅ 创建测试文档: {test_file}")
        
        try:
            # 2. 上传文档
            print("\n📤 步骤1: 上传文档...")
            with open(test_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=test_file.name, content_type='text/markdown')
                data.add_field('upload_only', 'false')
                data.add_field('generate_summary', 'true')
                data.add_field('create_index', 'true')
                data.add_field('deep_analysis', 'true')
                
                upload_url = f"{API_BASE}/api/v2/documents/upload?project_id={PROJECT_ID}"
                async with session.post(upload_url, data=data, headers=HEADERS) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        document_id = result['document_id']
                        pipeline_data = result.get('processing_pipeline')
                        pipeline_id = pipeline_data.get('pipeline_id') if pipeline_data else None
                        print(f"  ✅ 上传成功")
                        print(f"  📄 文档ID: {document_id}")
                        print(f"  🔧 管道ID: {pipeline_id}")
                        if pipeline_data:
                            print(f"  📊 处理阶段: {len(pipeline_data.get('stages', []))}个")
                    else:
                        error = await resp.text()
                        print(f"  ❌ 上传失败: {resp.status}")
                        print(f"  错误: {error}")
                        return
            
            # 3. 监控处理进度
            if pipeline_id:
                print("\n⏳ 步骤2: 监控处理进度...")
                completed = False
                start_time = time.time()
                
                for i in range(120):  # 最多等待10分钟
                    await asyncio.sleep(5)
                    
                    # 检查管道状态
                    status_url = f"{API_BASE}/api/v1/pipelines/{pipeline_id}/status"
                    async with session.get(status_url, headers=HEADERS) as resp:
                        if resp.status == 200:
                            status = await resp.json()
                            progress = status.get('overall_progress', 0)
                            current_stage = status.get('current_stage', 'unknown')
                            
                            print(f"  📊 进度: {progress:.1f}% - {current_stage}")
                            
                            # 检查各阶段状态
                            if status.get('stages'):
                                for stage in status['stages']:
                                    stage_type = stage['stage_type']
                                    stage_status = stage['status']
                                    stage_progress = stage['progress']
                                    print(f"    - {stage_type}: {stage_status} ({stage_progress}%)")
                                    
                                    if stage.get('error'):
                                        print(f"      ❌ 错误: {stage['error']}")
                            
                            if status.get('completed'):
                                completed = True
                                break
                
                duration = time.time() - start_time
                print(f"\n⏱️  总耗时: {duration:.2f}秒")
                
                if completed:
                    print("✅ 处理完成！")
                    
                    # 4. 验证各项结果
                    print("\n🔍 步骤3: 验证处理结果...")
                    
                    # 检查文档状态
                    doc_status_url = f"{API_BASE}/api/v1/documents/{document_id}/operations/status"
                    async with session.get(doc_status_url, headers=HEADERS) as resp:
                        if resp.status == 200:
                            doc_status = await resp.json()
                            print(f"  📄 文档状态: {doc_status['document_status']}")
                            ops_summary = doc_status['operations_summary']
                            print(f"  ✅ 摘要: {'完成' if ops_summary['summary_completed'] else '未完成'}")
                            print(f"  ✅ 索引: {'完成' if ops_summary['index_completed'] else '未完成'}")
                            print(f"  ✅ 分析: {'完成' if ops_summary['analysis_completed'] else '未完成'}")
                    
                    # 获取摘要结果
                    print("\n📝 摘要结果:")
                    summary_url = f"{API_BASE}/api/v1/documents/{document_id}/summary"
                    async with session.get(summary_url, headers=HEADERS) as resp:
                        if resp.status == 200:
                            summary_data = await resp.json()
                            print(f"  摘要: {summary_data['summary'][:200]}...")
                            print(f"  关键词: {', '.join(summary_data['keywords'][:5])}")
                    
                    # 获取分析结果
                    print("\n🧠 分析结果:")
                    analysis_url = f"{API_BASE}/api/v1/documents/{document_id}/analysis"
                    async with session.get(analysis_url, headers=HEADERS) as resp:
                        if resp.status == 200:
                            analysis_data = await resp.json()
                            if analysis_data.get('result'):
                                result = analysis_data['result']
                                print(f"  洞察数: {len(result.get('key_insights', []))}")
                                print(f"  行动项: {len(result.get('action_items', []))}")
                                
                                if result.get('key_insights'):
                                    print("\n  关键洞察:")
                                    for i, insight in enumerate(result['key_insights'][:3], 1):
                                        print(f"    {i}. {insight}")
                        else:
                            print(f"  ❌ 获取分析结果失败: {resp.status}")
                    
                    # 测试问答功能
                    print("\n💬 步骤4: 测试问答功能...")
                    qa_url = f"{API_BASE}/api/v1/qa/answer"
                    qa_data = {
                        "question": "这份报告主要讲了什么？有哪些关键技术？",
                        "project_id": PROJECT_ID
                    }
                    async with session.post(qa_url, json=qa_data, headers=HEADERS) as resp:
                        if resp.status == 200:
                            qa_result = await resp.json()
                            print(f"  问题: {qa_data['question']}")
                            print(f"  回答: {qa_result['answer'][:300]}...")
                            print(f"  来源数: {len(qa_result.get('sources', []))}")
                        else:
                            print(f"  ❌ 问答失败: {resp.status}")
                    
                    print("\n✅ 完整流程测试成功！")
                    
                else:
                    print("❌ 处理超时")
            
        finally:
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
                print(f"\n🧹 清理测试文件: {test_file}")

async def main():
    print("🔧 DPA完整流程测试")
    print(f"API服务器: {API_BASE}")
    print(f"项目ID: {PROJECT_ID}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    await test_complete_flow()

if __name__ == "__main__":
    asyncio.run(main())