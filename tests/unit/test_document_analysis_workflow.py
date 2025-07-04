"""
文档深度分析工作流单元测试
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.graphs.document_analysis_workflow import (
    DocumentAnalysisWorkflow,
    AnalysisState,
    AnalysisStage
)


class TestDocumentAnalysisWorkflow:
    """文档分析工作流测试类"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def workflow(self, mock_db_session):
        """创建工作流实例"""
        with patch('src.graphs.document_analysis_workflow.ChatOpenAI'):
            return DocumentAnalysisWorkflow(mock_db_session)
    
    @pytest.fixture
    def sample_state(self):
        """创建示例状态"""
        return {
            "document_id": "test_doc_001",
            "project_id": "test_project",
            "user_id": "test_user",
            "analysis_goal": "深入理解文档内容",
            "document_content": "这是一个测试文档，包含了一些重要的内容...",
            "structured_summary": {},
            "knowledge_graph": {},
            "deep_insights": [],
            "critical_findings": [],
            "integrated_knowledge": {},
            "final_output": {},
            "current_stage": AnalysisStage.PREPARATION,
            "stage_results": {},
            "errors": [],
            "warnings": [],
            "start_time": datetime.now(),
            "end_time": None,
            "total_tokens_used": 0
        }
    
    @pytest.mark.asyncio
    async def test_prepare_document(self, workflow, sample_state):
        """测试文档准备阶段"""
        # 模拟LLM响应
        workflow.fast_llm.ainvoke = AsyncMock(return_value=Mock(
            content='[{"chunk_id": 1, "content": "测试内容", "topic": "主题", "position": "第一章", "key_concepts": ["概念1"], "metadata_tags": ["标签1"]}]'
        ))
        
        result = await workflow.prepare_document(sample_state)
        
        assert result["current_stage"] == AnalysisStage.PREPARATION
        assert "preparation" in result["stage_results"]
        assert result["stage_results"]["preparation"]["chunk_count"] > 0
    
    @pytest.mark.asyncio
    async def test_macro_understanding(self, workflow, sample_state):
        """测试宏观理解阶段"""
        workflow.fast_llm.ainvoke = AsyncMock(return_value=Mock(content="这是一个摘要"))
        workflow.llm.ainvoke = AsyncMock(return_value=Mock(
            content='{"entities": {"概念1": {"type": "concept", "importance": 5}}, "relations": []}'
        ))
        
        result = await workflow.macro_understanding(sample_state)
        
        assert result["current_stage"] == AnalysisStage.MACRO_UNDERSTANDING
        assert "structured_summary" in result
        assert "knowledge_graph" in result
    
    @pytest.mark.asyncio
    async def test_deep_exploration(self, workflow, sample_state):
        """测试深度探索阶段"""
        sample_state["structured_summary"] = {"main_arguments": ["论点1", "论点2"]}
        sample_state["knowledge_graph"] = {"entities": {"概念1": {"type": "concept"}}}
        
        workflow.llm.ainvoke = AsyncMock(return_value=Mock(content='[]'))
        workflow._parse_questions = Mock(return_value=[
            {"question": "测试问题", "level": "basic", "purpose": "理解"}
        ])
        workflow.fast_llm.ainvoke = AsyncMock(return_value=Mock(content="测试答案"))
        
        result = await workflow.deep_exploration(sample_state)
        
        assert result["current_stage"] == AnalysisStage.DEEP_EXPLORATION
        assert "deep_insights" in result
    
    @pytest.mark.asyncio
    async def test_critical_analysis(self, workflow, sample_state):
        """测试批判性分析阶段"""
        sample_state["deep_insights"] = {"evidence_chains": []}
        
        workflow.llm.ainvoke = AsyncMock(return_value=Mock(content='[]'))
        
        result = await workflow.critical_analysis(sample_state)
        
        assert result["current_stage"] == AnalysisStage.CRITICAL_ANALYSIS
        assert "critical_findings" in result
        assert "overall_credibility" in result["critical_findings"]
    
    @pytest.mark.asyncio
    async def test_knowledge_integration(self, workflow, sample_state):
        """测试知识整合阶段"""
        sample_state["structured_summary"] = {}
        sample_state["deep_insights"] = {}
        sample_state["critical_findings"] = {}
        
        workflow.llm.ainvoke = AsyncMock(return_value=Mock(
            content='{"core_themes": [], "theme_relationships": [], "integrated_framework": {}, "innovations": []}'
        ))
        workflow.project_memory.get_or_create_project_memory = AsyncMock(
            return_value=Mock(key_concepts=[], learned_facts=[], total_documents=0)
        )
        
        result = await workflow.knowledge_integration(sample_state)
        
        assert result["current_stage"] == AnalysisStage.KNOWLEDGE_INTEGRATION
        assert "integrated_knowledge" in result
    
    @pytest.mark.asyncio
    async def test_output_generation(self, workflow, sample_state):
        """测试成果输出阶段"""
        sample_state["integrated_knowledge"] = {
            "novel_insights": [{"insight": "测试洞察"}],
            "actionable_recommendations": []
        }
        
        workflow.llm.ainvoke = AsyncMock(return_value=Mock(content="执行摘要内容"))
        workflow._determine_output_type = Mock(return_value="summary")
        workflow._prepare_visualization_data = Mock(return_value={})
        
        result = await workflow.output_generation(sample_state)
        
        assert result["current_stage"] == AnalysisStage.OUTPUT_GENERATION
        assert "final_output" in result
        assert "executive_summary" in result["final_output"]
    
    @pytest.mark.asyncio
    async def test_save_to_memory(self, workflow, sample_state):
        """测试保存到记忆系统"""
        sample_state["integrated_knowledge"] = {
            "novel_insights": [],
            "actionable_recommendations": []
        }
        sample_state["knowledge_graph"] = {"entities": {}}
        sample_state["final_output"] = {"executive_summary": "测试摘要"}
        
        workflow.project_memory.update_project_memory = AsyncMock()
        workflow.memory_service.create_memory = AsyncMock()
        
        result = await workflow.save_to_memory(sample_state)
        
        assert result["end_time"] is not None
        workflow.project_memory.update_project_memory.assert_called_once()
        workflow.memory_service.create_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, workflow, sample_state):
        """测试错误处理"""
        # 模拟LLM调用失败
        workflow.fast_llm.ainvoke = AsyncMock(side_effect=Exception("LLM调用失败"))
        
        result = await workflow.prepare_document(sample_state)
        
        assert len(result["errors"]) > 0
        assert "Preparation error" in result["errors"][0]
    
    def test_calculate_credibility_score(self, workflow):
        """测试可信度分数计算"""
        perspectives = []
        assumptions = [{"validity": "questionable"}, {"validity": "strong"}]
        gaps = ["gap1", "gap2"]
        
        score = workflow._calculate_credibility_score(perspectives, assumptions, gaps)
        
        # 2个gap扣0.2，1个questionable假设扣0.05，总扣0.25
        assert score == 0.75
    
    def test_determine_output_type(self, workflow):
        """测试输出类型判断"""
        assert workflow._determine_output_type("帮我做决策") == "action"
        assert workflow._determine_output_type("技术分析") == "technical"
        assert workflow._determine_output_type("简单总结") == "summary"
    
    def test_parse_questions(self, workflow):
        """测试问题解析"""
        questions = workflow._parse_questions("some response")
        
        assert len(questions) == 3
        assert questions[0]["level"] == "basic"
        assert questions[1]["level"] == "analysis"
        assert questions[2]["level"] == "synthesis"


@pytest.mark.asyncio
class TestWorkflowIntegration:
    """工作流集成测试"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def workflow(self, mock_db_session):
        """创建工作流实例"""
        with patch('src.graphs.document_analysis_workflow.ChatOpenAI'):
            workflow = DocumentAnalysisWorkflow(mock_db_session)
            # 模拟所有LLM调用
            workflow.llm.ainvoke = AsyncMock(return_value=Mock(content='{"result": "mocked"}'))
            workflow.fast_llm.ainvoke = AsyncMock(return_value=Mock(content='{"result": "mocked"}'))
            # 模拟记忆服务
            workflow.project_memory.get_or_create_project_memory = AsyncMock(
                return_value=Mock(key_concepts=[], learned_facts=[], total_documents=0)
            )
            workflow.project_memory.update_project_memory = AsyncMock()
            workflow.memory_service.create_memory = AsyncMock()
            return workflow
    
    async def test_full_workflow_execution(self, workflow):
        """测试完整工作流执行"""
        initial_state = {
            "document_id": "integration_test_doc",
            "project_id": "test_project",
            "user_id": "test_user",
            "analysis_goal": "全面分析测试",
            "document_content": "这是一份测试文档，用于集成测试...",
            "structured_summary": {},
            "knowledge_graph": {},
            "deep_insights": [],
            "critical_findings": [],
            "integrated_knowledge": {},
            "final_output": {},
            "current_stage": AnalysisStage.PREPARATION,
            "stage_results": {},
            "errors": [],
            "warnings": [],
            "start_time": datetime.now(),
            "end_time": None,
            "total_tokens_used": 0
        }
        
        # 模拟工作流中的辅助方法
        workflow._parse_questions = Mock(return_value=[])
        workflow._prepare_visualization_data = Mock(return_value={})
        workflow._calculate_credibility_score = Mock(return_value=0.8)
        workflow._determine_output_type = Mock(return_value="summary")
        
        # 执行工作流
        # 注意：由于LangGraph的compile()方法需要实际的图结构，
        # 在单元测试中我们直接调用各个阶段的方法
        result = initial_state
        result = await workflow.prepare_document(result)
        result = await workflow.macro_understanding(result)
        result = await workflow.deep_exploration(result)
        result = await workflow.critical_analysis(result)
        result = await workflow.knowledge_integration(result)
        result = await workflow.output_generation(result)
        result = await workflow.save_to_memory(result)
        
        # 验证所有阶段都执行了
        assert "preparation" in result["stage_results"]
        assert "macro_understanding" in result["stage_results"]
        assert "deep_exploration" in result["stage_results"]
        assert "critical_analysis" in result["stage_results"]
        assert "knowledge_integration" in result["stage_results"]
        assert "output_generation" in result["stage_results"]
        
        # 验证最终输出
        assert result["end_time"] is not None
        assert "final_output" in result
        assert len(result["errors"]) == 0  # 应该没有错误