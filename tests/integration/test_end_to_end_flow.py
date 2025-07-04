"""
端到端系统集成测试
测试完整的文档处理、分析、问答流程
"""

import pytest
import asyncio
import time
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.models.base import Base
from src.database.postgresql import get_db_session
from src.config.settings import get_settings


class TestEndToEndFlow:
    """端到端流程测试"""
    
    @pytest.fixture(scope="class")
    def test_db(self):
        """创建测试数据库"""
        # 使用SQLite内存数据库进行测试
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db_session] = override_get_db
        yield TestingSessionLocal
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def client(self, test_db):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_document(self):
        """示例文档内容"""
        return {
            "title": "人工智能在教育中的应用研究",
            "content": """
# 人工智能在教育中的应用研究

## 摘要
本文探讨了人工智能技术在现代教育中的应用，包括个性化学习、智能辅导系统和自动评估等方面。
研究表明，AI技术可以显著提升教育效率和学习效果。

## 1. 引言
随着人工智能技术的快速发展，教育领域正在经历深刻的变革。传统的"一刀切"教育模式
正在被个性化、智能化的教育方式所取代。

## 2. AI在教育中的主要应用
### 2.1 个性化学习
AI可以根据每个学生的学习进度、能力和兴趣，定制个性化的学习路径。

### 2.2 智能辅导系统
通过自然语言处理和机器学习，AI辅导系统可以回答学生问题，提供即时反馈。

### 2.3 自动评估与反馈
AI可以自动批改作业，分析学生的错误模式，提供针对性的改进建议。

## 3. 案例研究
### 3.1 可汗学院的AI应用
可汗学院使用AI技术为学生提供个性化的数学练习。

### 3.2 Duolingo的语言学习
Duolingo通过AI算法优化语言学习路径，提高学习效率。

## 4. 挑战与机遇
### 4.1 技术挑战
- 数据隐私保护
- 算法偏见问题
- 技术基础设施要求

### 4.2 教育公平性
AI技术有潜力缩小教育差距，但也可能加剧数字鸿沟。

## 5. 结论
人工智能在教育中的应用前景广阔，但需要谨慎处理相关挑战，确保技术服务于教育本质。

## 参考文献
1. Smith, J. (2023). AI in Education: A Comprehensive Review.
2. Zhang, L. (2023). Personalized Learning with AI.
""",
            "metadata": {
                "author": "测试作者",
                "date": "2025-07-04",
                "category": "教育科技",
                "language": "zh"
            }
        }
    
    def test_complete_document_flow(self, client, sample_document):
        """测试完整的文档处理流程"""
        
        # 1. 创建项目
        project_response = client.post("/api/v1/projects", json={
            "name": "教育AI研究项目",
            "description": "研究AI在教育领域的应用"
        })
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]
        
        # 2. 上传文档
        upload_response = client.post("/api/v1/documents/upload", json={
            "project_id": project_id,
            "title": sample_document["title"],
            "content": sample_document["content"],
            "metadata": sample_document["metadata"]
        })
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]
        
        # 3. 等待处理完成（简化处理）
        max_wait = 30  # 最多等待30秒
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status_response = client.get(f"/api/v1/documents/{document_id}/status")
            if status_response.json()["status"] == "completed":
                break
            time.sleep(1)
        
        assert status_response.json()["status"] == "completed"
        
        # 4. 启动文档分析
        analysis_response = client.post("/api/v1/analysis/start", json={
            "document_id": document_id,
            "project_id": project_id,
            "user_id": "test_user",
            "analysis_goal": "深入理解AI在教育中的应用和挑战"
        })
        assert analysis_response.status_code == 200
        analysis_id = analysis_response.json()["analysis_id"]
        
        # 5. 等待分析完成
        max_wait = 60  # 分析可能需要更长时间
        start_time = time.time()
        while time.time() - start_time < max_wait:
            analysis_status = client.get(f"/api/v1/analysis/status/{analysis_id}")
            if analysis_status.json()["status"] == "completed":
                break
            time.sleep(2)
        
        # 6. 获取分析结果
        results_response = client.get(f"/api/v1/analysis/results/{analysis_id}")
        assert results_response.status_code == 200
        analysis_results = results_response.json()
        
        # 验证分析结果
        assert "executive_summary" in analysis_results
        assert "key_findings" in analysis_results
        assert len(analysis_results["key_findings"]) > 0
        
        # 7. 测试问答功能
        qa_response = client.post("/api/v1/qa/ask", json={
            "question": "AI在教育中的主要应用有哪些？",
            "project_id": project_id,
            "user_id": "test_user"
        })
        assert qa_response.status_code == 200
        qa_result = qa_response.json()
        
        assert qa_result["success"] is True
        assert "个性化学习" in qa_result["answer"]
        assert len(qa_result["sources"]) > 0
        
        # 8. 测试记忆增强问答
        enhanced_qa_response = client.post("/api/v1/qa/enhanced/ask", json={
            "question": "基于之前的分析，AI教育面临的最大挑战是什么？",
            "project_id": project_id,
            "user_id": "test_user"
        })
        assert enhanced_qa_response.status_code == 200
        enhanced_result = enhanced_qa_response.json()
        
        assert enhanced_result["success"] is True
        assert "数据隐私" in enhanced_result["answer"] or "算法偏见" in enhanced_result["answer"]
        
        # 9. 验证记忆系统
        memory_response = client.get(f"/api/v1/memory/project/{project_id}")
        assert memory_response.status_code == 200
        project_memory = memory_response.json()
        
        assert project_memory["total_documents"] >= 1
        assert len(project_memory["key_concepts"]) > 0
        assert "AI" in str(project_memory["key_concepts"])
    
    def test_batch_document_processing(self, client):
        """测试批量文档处理"""
        
        # 创建项目
        project_response = client.post("/api/v1/projects", json={
            "name": "批量处理测试项目"
        })
        project_id = project_response.json()["id"]
        
        # 批量上传文档
        documents = []
        for i in range(3):
            doc_response = client.post("/api/v1/documents/upload", json={
                "project_id": project_id,
                "title": f"测试文档 {i+1}",
                "content": f"这是第{i+1}个测试文档的内容。包含一些关键信息{i+1}。",
                "metadata": {"index": i+1}
            })
            documents.append(doc_response.json()["document_id"])
        
        # 等待所有文档处理完成
        time.sleep(5)
        
        # 测试跨文档问答
        qa_response = client.post("/api/v1/qa/ask", json={
            "question": "所有文档中都提到了什么关键信息？",
            "project_id": project_id,
            "user_id": "test_user"
        })
        
        assert qa_response.status_code == 200
        assert qa_response.json()["success"] is True
    
    @pytest.mark.performance
    def test_system_performance(self, client, sample_document):
        """测试系统性能"""
        
        # 创建测试项目
        project_response = client.post("/api/v1/projects", json={
            "name": "性能测试项目"
        })
        project_id = project_response.json()["id"]
        
        # 记录性能指标
        metrics = {
            "document_upload_times": [],
            "qa_response_times": [],
            "analysis_times": []
        }
        
        # 测试文档上传性能
        for i in range(5):
            start = time.time()
            response = client.post("/api/v1/documents/upload", json={
                "project_id": project_id,
                "title": f"性能测试文档 {i}",
                "content": sample_document["content"],
                "metadata": {"test_index": i}
            })
            end = time.time()
            metrics["document_upload_times"].append(end - start)
            assert response.status_code == 200
        
        # 等待处理
        time.sleep(10)
        
        # 测试问答响应时间
        questions = [
            "AI在教育中的应用有哪些？",
            "个性化学习如何实现？",
            "教育AI面临什么挑战？",
            "可汗学院如何使用AI？",
            "AI如何影响教育公平？"
        ]
        
        for question in questions:
            start = time.time()
            response = client.post("/api/v1/qa/ask", json={
                "question": question,
                "project_id": project_id,
                "user_id": "test_user"
            })
            end = time.time()
            metrics["qa_response_times"].append(end - start)
            assert response.status_code == 200
        
        # 计算性能统计
        avg_upload_time = sum(metrics["document_upload_times"]) / len(metrics["document_upload_times"])
        avg_qa_time = sum(metrics["qa_response_times"]) / len(metrics["qa_response_times"])
        
        # 性能断言
        assert avg_upload_time < 2.0, f"文档上传平均时间 {avg_upload_time}s 超过2秒"
        assert avg_qa_time < 3.0, f"问答平均响应时间 {avg_qa_time}s 超过3秒"
        
        # 输出性能报告
        print("\n=== 性能测试报告 ===")
        print(f"文档上传平均时间: {avg_upload_time:.2f}秒")
        print(f"问答响应平均时间: {avg_qa_time:.2f}秒")
        print(f"最慢的问答响应: {max(metrics['qa_response_times']):.2f}秒")
    
    def test_error_handling_and_recovery(self, client):
        """测试错误处理和恢复机制"""
        
        # 测试无效输入
        response = client.post("/api/v1/documents/upload", json={
            "project_id": "invalid_id",
            "title": "",  # 空标题
            "content": ""  # 空内容
        })
        assert response.status_code == 400
        
        # 测试不存在的文档
        response = client.get("/api/v1/documents/non_existent_id/status")
        assert response.status_code == 404
        
        # 测试分析不存在的文档
        response = client.post("/api/v1/analysis/start", json={
            "document_id": "non_existent",
            "project_id": "invalid",
            "user_id": "test"
        })
        assert response.status_code in [400, 404]
        
        # 测试问答系统的错误处理
        response = client.post("/api/v1/qa/ask", json={
            "question": "",  # 空问题
            "project_id": "invalid"
        })
        assert response.status_code == 400
    
    def test_concurrent_requests(self, client):
        """测试并发请求处理"""
        import concurrent.futures
        
        # 创建项目
        project_response = client.post("/api/v1/projects", json={
            "name": "并发测试项目"
        })
        project_id = project_response.json()["id"]
        
        # 上传一个文档
        doc_response = client.post("/api/v1/documents/upload", json={
            "project_id": project_id,
            "title": "并发测试文档",
            "content": "这是用于并发测试的文档内容。包含多个主题和信息。"
        })
        document_id = doc_response.json()["document_id"]
        
        # 等待处理
        time.sleep(5)
        
        # 并发问答请求
        def ask_question(question):
            return client.post("/api/v1/qa/ask", json={
                "question": question,
                "project_id": project_id,
                "user_id": f"user_{question[:5]}"
            })
        
        questions = [
            "文档的主要内容是什么？",
            "有哪些关键主题？",
            "文档提到了什么信息？",
            "这是什么类型的文档？",
            "文档的目的是什么？"
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(ask_question, q) for q in questions]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 验证所有请求都成功
        for result in results:
            assert result.status_code == 200
            assert result.json()["success"] is True


class TestCachePerformance:
    """缓存性能测试"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cache_effectiveness(self, client):
        """测试缓存有效性"""
        
        # 创建项目并上传文档
        project_response = client.post("/api/v1/projects", json={
            "name": "缓存测试项目"
        })
        project_id = project_response.json()["id"]
        
        doc_response = client.post("/api/v1/documents/upload", json={
            "project_id": project_id,
            "title": "缓存测试文档",
            "content": "这是一个用于测试缓存系统的文档。包含重要信息。"
        })
        
        time.sleep(3)  # 等待处理
        
        # 相同问题多次查询
        question = "文档包含什么重要信息？"
        
        # 第一次查询（缓存未命中）
        start1 = time.time()
        response1 = client.post("/api/v1/qa/ask", json={
            "question": question,
            "project_id": project_id,
            "user_id": "cache_test_user"
        })
        time1 = time.time() - start1
        
        # 第二次查询（应该命中缓存）
        start2 = time.time()
        response2 = client.post("/api/v1/qa/ask", json={
            "question": question,
            "project_id": project_id,
            "user_id": "cache_test_user"
        })
        time2 = time.time() - start2
        
        # 验证缓存效果
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["answer"] == response2.json()["answer"]
        assert time2 < time1 * 0.5, f"缓存未生效：第一次{time1:.2f}s，第二次{time2:.2f}s"
        
        print(f"\n缓存性能提升: {((time1 - time2) / time1 * 100):.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])