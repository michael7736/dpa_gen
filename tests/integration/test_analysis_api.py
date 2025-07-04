"""
文档分析API集成测试
"""

import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

from src.api.main import app


class TestAnalysisAPI:
    """文档分析API测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_workflow(self):
        """模拟文档分析工作流"""
        with patch('src.api.routes.analysis.DocumentAnalysisWorkflow') as mock:
            workflow_instance = Mock()
            workflow_instance.app = Mock()
            workflow_instance.app.ainvoke = AsyncMock(return_value={
                "final_output": {
                    "executive_summary": "测试摘要",
                    "key_findings": []
                },
                "integrated_knowledge": {
                    "novel_insights": [{"insight": "测试洞察", "confidence": 0.8}]
                },
                "errors": [],
                "end_time": datetime.now(),
                "start_time": datetime.now()
            })
            mock.return_value = workflow_instance
            yield workflow_instance
    
    def test_start_analysis(self, client, mock_workflow):
        """测试启动文档分析"""
        request_data = {
            "document_id": "test_doc_001",
            "project_id": "test_project",
            "user_id": "test_user",
            "analysis_goal": "深入理解文档内容",
            "analysis_type": "comprehensive",
            "output_formats": ["executive_summary", "detailed_report"]
        }
        
        response = client.post("/api/v1/analysis/start", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "started"
        assert "preview" in data
    
    def test_get_analysis_status(self, client):
        """测试获取分析状态"""
        # 首先启动一个分析
        request_data = {
            "document_id": "test_doc_002",
            "project_id": "test_project",
            "user_id": "test_user",
            "analysis_goal": "测试分析"
        }
        
        start_response = client.post("/api/v1/analysis/start", json=request_data)
        analysis_id = start_response.json()["analysis_id"]
        
        # 获取状态
        response = client.get(f"/api/v1/analysis/status/{analysis_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == analysis_id
        assert "status" in data
        assert "progress" in data
    
    def test_get_analysis_results(self, client, mock_workflow):
        """测试获取分析结果"""
        # 模拟已完成的分析
        from src.api.routes.analysis import running_analyses
        analysis_id = "completed_analysis_001"
        running_analyses[analysis_id] = {
            "status": "completed",
            "state": {
                "document_id": "test_doc",
                "analysis_goal": "测试",
                "final_output": {"executive_summary": "测试摘要"},
                "integrated_knowledge": {
                    "novel_insights": [{"insight": "洞察1", "confidence": 0.9}],
                    "actionable_recommendations": [{"recommendation": "建议1"}]
                },
                "knowledge_graph": {"entities": {}, "relations": []},
                "end_time": datetime.now(),
                "start_time": datetime.now()
            },
            "progress": 100.0
        }
        
        response = client.get(f"/api/v1/analysis/results/{analysis_id}?include_details=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == analysis_id
        assert "executive_summary" in data
        assert "key_findings" in data
        assert "detailed_results" in data
    
    def test_analyze_text_directly(self, client, mock_workflow):
        """测试直接分析文本"""
        response = client.post(
            "/api/v1/analysis/analyze-text",
            json={
                "text": "这是一段测试文本",
                "analysis_type": "quick",
                "user_id": "test_user"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "knowledge_graph" in data
        assert "key_concepts" in data
    
    def test_get_analysis_prompts(self, client):
        """测试获取分析提示词"""
        # 获取特定类别的提示词
        response = client.get("/api/v1/analysis/prompts/preparation")
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "preparation"
        assert "prompts" in data
        
        # 获取特定提示词
        response = client.get("/api/v1/analysis/prompts/preparation?prompt_name=intelligent_chunking")
        
        assert response.status_code == 200
        data = response.json()
        assert "prompt" in data
    
    def test_execute_custom_prompt(self, client):
        """测试执行自定义提示词"""
        response = client.post(
            "/api/v1/analysis/custom-prompt",
            json={
                "document_id": "test_doc",
                "prompt": "请分析这个文档的主要观点",
                "context": {"focus": "技术创新"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test_doc"
        assert "analysis" in data
    
    def test_get_analysis_templates(self, client):
        """测试获取分析模板"""
        response = client.get("/api/v1/analysis/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0
        
        # 验证模板结构
        template = data["templates"][0]
        assert "id" in template
        assert "name" in template
        assert "description" in template
        assert "focus_areas" in template
        assert "output_formats" in template
    
    def test_error_handling(self, client):
        """测试错误处理"""
        # 测试获取不存在的分析
        response = client.get("/api/v1/analysis/status/non_existent_id")
        assert response.status_code == 404
        
        # 测试获取未完成分析的结果
        from src.api.routes.analysis import running_analyses
        analysis_id = "running_analysis"
        running_analyses[analysis_id] = {
            "status": "running",
            "state": {},
            "progress": 50.0
        }
        
        response = client.get(f"/api/v1/analysis/results/{analysis_id}")
        assert response.status_code == 400
        assert "still running" in response.json()["detail"]


@pytest.mark.asyncio
class TestAnalysisWorkflowIntegration:
    """分析工作流完整集成测试"""
    
    @pytest.fixture
    async def db_session(self):
        """创建测试数据库会话"""
        # 在实际测试中，这里应该创建测试数据库连接
        return Mock()
    
    async def test_complete_analysis_flow(self, db_session):
        """测试完整的分析流程"""
        from src.graphs.document_analysis_workflow import DocumentAnalysisWorkflow
        
        # 创建工作流实例（使用模拟的LLM）
        with patch('src.graphs.document_analysis_workflow.ChatOpenAI') as mock_llm:
            # 设置模拟响应
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value=Mock(content='{"result": "test"}'))
            mock_llm.return_value = mock_instance
            
            workflow = DocumentAnalysisWorkflow(db_session)
            
            # 模拟必要的服务
            workflow.project_memory.get_or_create_project_memory = AsyncMock(
                return_value=Mock(key_concepts=[], learned_facts=[], total_documents=0)
            )
            workflow.project_memory.update_project_memory = AsyncMock()
            workflow.memory_service.create_memory = AsyncMock()
            
            # 准备初始状态
            initial_state = {
                "document_id": "integration_test",
                "project_id": "test_project",
                "user_id": "test_user",
                "analysis_goal": "完整流程测试",
                "document_content": "这是一个用于集成测试的文档内容...",
                "structured_summary": {},
                "knowledge_graph": {},
                "deep_insights": [],
                "critical_findings": [],
                "integrated_knowledge": {},
                "final_output": {},
                "current_stage": "preparation",
                "stage_results": {},
                "errors": [],
                "warnings": [],
                "start_time": datetime.now(),
                "end_time": None,
                "total_tokens_used": 0
            }
            
            # 执行各个阶段
            state = await workflow.prepare_document(initial_state)
            assert "preparation" in state["stage_results"]
            
            state = await workflow.macro_understanding(state)
            assert "structured_summary" in state
            
            state = await workflow.deep_exploration(state)
            assert "deep_insights" in state
            
            state = await workflow.critical_analysis(state)
            assert "critical_findings" in state
            
            state = await workflow.knowledge_integration(state)
            assert "integrated_knowledge" in state
            
            state = await workflow.output_generation(state)
            assert "final_output" in state
            
            state = await workflow.save_to_memory(state)
            assert state["end_time"] is not None