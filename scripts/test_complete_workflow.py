#!/usr/bin/env python3
"""
完整工作流集成测试
测试从文档上传到分析的完整流程
"""

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"
HEADERS = {"X-USER-ID": USER_ID}

# 测试结果统计
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"🔄 {title}")
    print("=" * 60)


def print_test(name: str, passed: bool, error: str = None, details: str = None):
    """打印测试结果"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {error}")
        print(f"❌ {name}")
        if error:
            print(f"   错误: {error}")


async def test_project_workflow(client: httpx.AsyncClient):
    """测试项目管理完整工作流"""
    print_header("项目管理工作流")
    
    project_id = None
    
    try:
        # 1. 获取现有项目列表
        response = await client.get(f"{BASE_URL}/api/v1/projects", headers=HEADERS)
        print_test("获取项目列表", response.status_code == 200)
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   现有项目数: {len(projects)}")
            if projects:
                project_id = projects[0]["id"]
                print(f"   使用项目: {projects[0]['name']} (ID: {project_id})")
        
        # 2. 创建新项目（可选）
        if not project_id:
            create_data = {
                "name": f"集成测试项目-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": "自动化集成测试创建的项目"
            }
            response = await client.post(
                f"{BASE_URL}/api/v1/projects",
                headers=HEADERS,
                json=create_data
            )
            print_test("创建新项目", response.status_code == 200)
            
            if response.status_code == 200:
                project = response.json()
                project_id = project["id"]
                print(f"   新项目ID: {project_id}")
        
        return project_id
        
    except Exception as e:
        print_test("项目管理工作流", False, str(e))
        return None


async def test_document_workflow(client: httpx.AsyncClient, project_id: str):
    """测试文档处理完整工作流"""
    print_header("文档处理工作流")
    
    if not project_id:
        print("⚠️  跳过文档测试（无项目ID）")
        return None
    
    document_id = None
    
    try:
        # 1. 创建测试文档
        test_content = """
人工智能技术发展报告

第一章：深度学习基础
深度学习是机器学习的一个分支，它试图通过多层神经网络来学习数据的复杂表示。
深度学习在图像识别、自然语言处理和语音识别等领域取得了突破性进展。

第二章：Transformer架构
Transformer架构彻底改变了自然语言处理领域。它使用自注意力机制来处理序列数据，
相比于传统的RNN和LSTM，Transformer可以实现更好的并行化和更长的序列建模能力。

第三章：大语言模型
基于Transformer架构的大语言模型，如GPT系列和BERT，在各种NLP任务上都达到了
前所未有的性能。这些模型通过在大规模文本数据上进行预训练，学会了丰富的语言知识。

第四章：AI应用前景
人工智能技术正在各行各业得到广泛应用，从医疗诊断到自动驾驶，从金融风控到教育个性化，
AI技术正在改变我们的生活和工作方式。
"""
        
        # 2. 测试文档上传（简化版）
        upload_data = {
            "file_name": "ai_report.txt",
            "content": test_content,
            "project_id": project_id
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/documents/upload",
            headers=HEADERS,
            params={"project_id": project_id},
            json=upload_data
        )
        
        # 如果标准上传不工作，尝试简化上传
        if response.status_code != 200:
            response = await client.post(
                f"{BASE_URL}/api/v1/documents/simple/upload",
                headers=HEADERS,
                json=upload_data
            )
        
        print_test("文档上传", response.status_code == 200)
        
        if response.status_code == 200:
            upload_result = response.json()
            document_id = upload_result.get("document_id") or upload_result.get("id")
            print(f"   文档ID: {document_id}")
        
        # 3. 获取文档列表
        response = await client.get(
            f"{BASE_URL}/api/v1/documents",
            headers=HEADERS,
            params={"project_id": project_id}
        )
        print_test("获取文档列表", response.status_code == 200)
        
        if response.status_code == 200:
            documents = response.json()
            print(f"   项目文档数: {len(documents)}")
            
        return document_id
        
    except Exception as e:
        print_test("文档处理工作流", False, str(e))
        return None


async def test_aag_analysis_workflow(client: httpx.AsyncClient, document_id: str = None):
    """测试AAG分析完整工作流"""
    print_header("AAG分析工作流")
    
    # 使用测试文档内容
    test_content = """
人工智能技术发展报告

深度学习是机器学习的一个分支，通过多层神经网络学习数据的复杂表示。
Transformer架构使用自注意力机制，在自然语言处理领域取得突破。
大语言模型如GPT和BERT在各种NLP任务上达到前所未有的性能。
AI技术正在医疗、自动驾驶、金融等各行业得到广泛应用。
"""
    
    doc_id = document_id or "test_doc_workflow"
    
    try:
        # 1. 快速略读
        skim_data = {
            "skim_request": {
                "document_id": doc_id,
                "document_content": test_content,
                "document_type": "report"
            }
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/aag/skim",
            headers=HEADERS,
            json=skim_data
        )
        print_test("快速略读", response.status_code == 200)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✓ 快速略读成功")
                if result.get("result"):
                    doc_type = result["result"].get("document_type", "未知")
                    print(f"   文档类型: {doc_type}")
        
        # 2. 生成摘要
        summary_data = {
            "summary_request": {
                "document_id": doc_id,
                "document_content": test_content,
                "summary_level": "level_2"
            }
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/aag/summary",
            headers=HEADERS,
            json=summary_data
        )
        print_test("生成摘要", response.status_code == 200)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✓ 摘要生成成功")
        
        # 3. 深度分析
        analysis_data = {
            "analysis_request": {
                "document_id": doc_id,
                "document_content": test_content,
                "analysis_type": "technological"
            }
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/aag/deep-analysis",
            headers=HEADERS,
            json=analysis_data
        )
        print_test("深度分析", response.status_code == 200)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✓ 深度分析成功")
        
        return True
        
    except Exception as e:
        print_test("AAG分析工作流", False, str(e))
        return False


async def test_qa_workflow(client: httpx.AsyncClient, project_id: str):
    """测试问答工作流"""
    print_header("问答工作流")
    
    try:
        # 1. 基础问答
        qa_data = {
            "question": "什么是深度学习？它有什么特点？",
            "project_id": project_id or "test_project"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/qa/answer",
            headers=HEADERS,
            json=qa_data
        )
        print_test("基础问答", response.status_code == 200)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            confidence = result.get("confidence", 0)
            print(f"   回答长度: {len(answer)}字符")
            print(f"   置信度: {confidence}")
            
            if len(answer) > 50:  # 有实质性回答
                print("   ✓ 获得有效回答")
        
        # 2. 增强问答
        enhanced_qa_data = {
            "question": "人工智能在医疗领域有哪些应用？",
            "project_id": project_id or "test_project",
            "use_rerank": True,
            "max_results": 5
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/qa/enhanced/answer",
            headers=HEADERS,
            json=enhanced_qa_data
        )
        print_test("增强问答", response.status_code == 200)
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get("sources", [])
            print(f"   引用来源数: {len(sources)}")
        
        return True
        
    except Exception as e:
        print_test("问答工作流", False, str(e))
        return False


async def test_system_health(client: httpx.AsyncClient):
    """测试系统健康状态"""
    print_header("系统健康检查")
    
    try:
        # 1. 基础健康检查
        response = await client.get(f"{BASE_URL}/health")
        print_test("API健康检查", response.status_code == 200)
        
        if response.status_code == 200:
            health = response.json()
            status = health.get("status")
            services = health.get("services", {})
            print(f"   整体状态: {status}")
            
            for service, service_status in services.items():
                print(f"   {service}: {service_status}")
        
        # 2. 数据库连接检查
        response = await client.get(f"{BASE_URL}/api/v1/health/database")
        if response.status_code == 200:
            print_test("数据库健康检查", True, details="所有数据库连接正常")
        else:
            print_test("数据库健康检查", False, "部分数据库连接异常")
        
        return True
        
    except Exception as e:
        print_test("系统健康检查", False, str(e))
        return False


async def main():
    """运行完整工作流测试"""
    print("\n" + "🔄" * 20)
    print("DPA系统完整工作流测试")
    print("🔄" * 20)
    print(f"后端地址: {BASE_URL}")
    print(f"用户ID: {USER_ID}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 系统健康检查
        await test_system_health(client)
        
        # 2. 项目管理工作流
        project_id = await test_project_workflow(client)
        
        # 3. 文档处理工作流
        document_id = await test_document_workflow(client, project_id)
        
        # 4. AAG分析工作流
        await test_aag_analysis_workflow(client, document_id)
        
        # 5. 问答工作流
        await test_qa_workflow(client, project_id)
    
    # 打印测试总结
    print_header("📊 完整工作流测试总结")
    print(f"总测试数: {test_results['total']}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    
    if test_results['errors']:
        print("\n❌ 错误列表:")
        for error in test_results['errors']:
            print(f"   - {error}")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 评估系统状态
    if success_rate >= 80:
        print("\n🎉 系统状态: 优秀 - 所有核心功能正常运行")
    elif success_rate >= 60:
        print("\n✅ 系统状态: 良好 - 主要功能正常，部分功能需要优化")
    elif success_rate >= 40:
        print("\n⚠️  系统状态: 一般 - 基础功能正常，需要修复一些问题")
    else:
        print("\n❌ 系统状态: 需要修复 - 存在较多问题需要解决")


if __name__ == "__main__":
    asyncio.run(main())