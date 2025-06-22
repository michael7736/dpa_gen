"""
集成测试
验证知识引擎的核心功能
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from src.core.knowledge_index import create_knowledge_index_service, VectorConfig
from src.core.research_planner import create_research_planner_service, ResearchContext
from src.core.memory_system import create_memory_system_service
from src.services.document_parser import DocumentParserService
from src.services.file_storage import FileStorageService

class TestKnowledgeEngine:
    """知识引擎集成测试"""
    
    @pytest.fixture
    async def setup_services(self):
        """设置测试服务"""
        # 创建向量配置
        vector_config = VectorConfig(
            model_name="text-embedding-ada-002",
            dimension=1536,
            distance_metric="cosine",
            batch_size=10
        )
        
        # 创建服务
        knowledge_service = create_knowledge_index_service(vector_config)
        research_planner = create_research_planner_service(
            knowledge_service,
            llm_config={"model_name": "gpt-3.5-turbo", "temperature": 0.7}
        )
        memory_system = create_memory_system_service(
            knowledge_service.vector_service.embedding_service,
            knowledge_service.vector_service.vector_store
        )
        document_parser = DocumentParserService()
        file_storage = FileStorageService()
        
        return {
            "knowledge_service": knowledge_service,
            "research_planner": research_planner,
            "memory_system": memory_system,
            "document_parser": document_parser,
            "file_storage": file_storage
        }
    
    @pytest.mark.asyncio
    async def test_document_indexing(self, setup_services):
        """测试文档索引功能"""
        services = await setup_services
        knowledge_service = services["knowledge_service"]
        
        # 测试文档内容
        test_content = """
        # 人工智能概述
        
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支。
        
        ## 机器学习
        
        机器学习是人工智能的一个重要子领域。
        
        ### 深度学习
        
        深度学习使用神经网络进行学习。
        
        ## 自然语言处理
        
        自然语言处理（NLP）处理人类语言。
        """
        
        # 索引文档
        result = await knowledge_service.index_document(
            document_id="test_doc_1",
            content=test_content,
            metadata={"title": "AI概述", "author": "测试"}
        )
        
        # 验证结果
        assert result["document_id"] == "test_doc_1"
        assert result["chunks_count"] > 0
        assert len(result["point_ids"]) == result["chunks_count"]
        
        # 获取文档大纲
        outline = knowledge_service.get_document_outline("test_doc_1")
        assert outline["document_id"] == "test_doc_1"
        assert len(outline["structure"]) > 0
        
        print(f"✅ 文档索引测试通过: 生成 {result['chunks_count']} 个块")
    
    @pytest.mark.asyncio
    async def test_knowledge_search(self, setup_services):
        """测试知识搜索功能"""
        services = await setup_services
        knowledge_service = services["knowledge_service"]
        
        # 先索引一些文档
        test_docs = [
            {
                "id": "doc_ai",
                "content": "人工智能是模拟人类智能的技术。机器学习是AI的核心技术。",
                "metadata": {"topic": "AI"}
            },
            {
                "id": "doc_ml", 
                "content": "机器学习包括监督学习、无监督学习和强化学习。深度学习是机器学习的子集。",
                "metadata": {"topic": "ML"}
            },
            {
                "id": "doc_nlp",
                "content": "自然语言处理用于理解和生成人类语言。包括文本分析、语音识别等。",
                "metadata": {"topic": "NLP"}
            }
        ]
        
        for doc in test_docs:
            await knowledge_service.index_document(
                document_id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"]
            )
        
        # 测试搜索
        search_results = await knowledge_service.search(
            query="什么是机器学习？",
            search_type="vector",
            k=5,
            include_hierarchy=True
        )
        
        # 验证搜索结果
        assert search_results["total_results"] > 0
        assert "机器学习" in search_results["results"][0]["document"].page_content
        
        print(f"✅ 知识搜索测试通过: 找到 {search_results['total_results']} 个相关结果")
    
    @pytest.mark.asyncio
    async def test_research_planning(self, setup_services):
        """测试研究规划功能"""
        services = await setup_services
        research_planner = services["research_planner"]
        
        # 创建研究上下文
        context = ResearchContext(
            domain="人工智能",
            keywords=["机器学习", "深度学习", "神经网络"],
            existing_knowledge=["基础数学", "编程基础"],
            constraints={"时间": "3个月", "资源": "有限"},
            preferences={"方法": "理论结合实践"}
        )
        
        # 创建研究计划
        plan = await research_planner.create_research_plan(
            research_question="如何构建一个有效的深度学习模型？",
            context=context
        )
        
        # 验证计划
        assert plan.plan_id is not None
        assert plan.research_question == "如何构建一个有效的深度学习模型？"
        assert len(plan.tasks) > 0
        assert plan.current_phase.value == "planning"
        
        # 获取计划状态
        status = research_planner.get_plan_status(plan.plan_id)
        assert status["plan_id"] == plan.plan_id
        assert status["task_statistics"]["total"] == len(plan.tasks)
        
        print(f"✅ 研究规划测试通过: 创建计划 {plan.plan_id}，包含 {len(plan.tasks)} 个任务")
    
    @pytest.mark.asyncio
    async def test_memory_system(self, setup_services):
        """测试记忆系统功能"""
        services = await setup_services
        memory_system = services["memory_system"]
        
        # 存储情节记忆
        episode_id = await memory_system.store_episodic_memory(
            title="学习深度学习",
            description="今天学习了深度学习的基础概念，包括神经网络、反向传播等",
            events=[
                {"action": "阅读", "object": "深度学习教程", "time": "09:00"},
                {"action": "实践", "object": "神经网络代码", "time": "14:00"}
            ],
            context={
                "participants": ["学习者"],
                "location": "在线",
                "concepts": ["深度学习", "神经网络", "反向传播"],
                "significance": 0.8
            }
        )
        
        # 存储语义记忆
        concept_id = await memory_system.store_semantic_memory(
            concept_name="神经网络",
            definition="由多个神经元组成的计算模型，用于模拟人脑的信息处理",
            properties={
                "类型": "计算模型",
                "应用": ["图像识别", "自然语言处理"],
                "特点": ["非线性", "可学习"]
            },
            context={
                "examples": ["多层感知机", "卷积神经网络"],
                "relationships": {"包含": ["神经元", "权重", "偏置"]}
            }
        )
        
        # 搜索记忆
        search_results = await memory_system.retrieve_relevant_memories(
            query="神经网络的学习过程",
            k=5
        )
        
        # 验证结果
        assert episode_id is not None
        assert concept_id is not None
        assert len(search_results) > 0
        
        # 获取统计信息
        stats = memory_system.get_memory_statistics()
        assert stats["total_memories"] >= 2
        assert stats["episodic_count"] >= 1
        assert stats["semantic_count"] >= 1
        
        print(f"✅ 记忆系统测试通过: 存储 {stats['total_memories']} 个记忆")
    
    @pytest.mark.asyncio
    async def test_memory_consolidation(self, setup_services):
        """测试记忆巩固功能"""
        services = await setup_services
        memory_system = services["memory_system"]
        
        # 存储多个相关的情节记忆
        episodes = [
            {
                "title": "学习CNN",
                "description": "学习卷积神经网络的原理和应用",
                "concepts": ["CNN", "卷积", "池化"]
            },
            {
                "title": "实践CNN",
                "description": "用CNN做图像分类项目",
                "concepts": ["CNN", "图像分类", "训练"]
            },
            {
                "title": "优化CNN",
                "description": "调整CNN参数提高性能",
                "concepts": ["CNN", "超参数", "优化"]
            }
        ]
        
        for episode in episodes:
            await memory_system.store_episodic_memory(
                title=episode["title"],
                description=episode["description"],
                events=[],
                context={
                    "concepts": episode["concepts"],
                    "significance": 0.8
                }
            )
        
        # 执行记忆巩固
        consolidation_result = await memory_system.consolidate_memories()
        
        # 验证巩固结果
        if consolidation_result["consolidated"] > 0:
            assert "new_concepts" in consolidation_result
            print(f"✅ 记忆巩固测试通过: 巩固了 {consolidation_result['consolidated']} 个概念")
        else:
            print("✅ 记忆巩固测试通过: 没有需要巩固的记忆")
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, setup_services):
        """测试端到端工作流"""
        services = await setup_services
        knowledge_service = services["knowledge_service"]
        research_planner = services["research_planner"]
        memory_system = services["memory_system"]
        
        # 1. 索引知识文档
        knowledge_content = """
        # 深度学习研究现状
        
        深度学习在近年来取得了显著进展。
        
        ## 技术突破
        
        - Transformer架构革命了NLP领域
        - 扩散模型在图像生成方面表现出色
        - 大语言模型展现了强大的通用能力
        
        ## 应用领域
        
        深度学习已广泛应用于：
        - 计算机视觉
        - 自然语言处理  
        - 语音识别
        - 推荐系统
        
        ## 未来挑战
        
        - 模型可解释性
        - 计算效率
        - 数据隐私
        """
        
        await knowledge_service.index_document(
            document_id="dl_research",
            content=knowledge_content,
            metadata={"title": "深度学习研究现状", "type": "综述"}
        )
        
        # 2. 创建研究计划
        context = ResearchContext(
            domain="深度学习",
            keywords=["Transformer", "扩散模型", "大语言模型"],
            existing_knowledge=["机器学习基础"],
            constraints={"时间": "6个月"},
            preferences={"重点": "实际应用"}
        )
        
        plan = await research_planner.create_research_plan(
            research_question="如何提高深度学习模型的可解释性？",
            context=context
        )
        
        # 3. 存储研究记忆
        await memory_system.store_episodic_memory(
            title="深度学习文献调研",
            description="调研了深度学习的最新进展和挑战",
            events=[{"action": "阅读", "object": "研究论文"}],
            context={
                "concepts": ["深度学习", "可解释性", "Transformer"],
                "significance": 0.9
            }
        )
        
        # 4. 知识搜索验证
        search_results = await knowledge_service.search(
            query="深度学习的未来挑战是什么？",
            k=3
        )
        
        # 5. 记忆搜索验证
        memory_results = await memory_system.retrieve_relevant_memories(
            query="深度学习研究",
            k=3
        )
        
        # 验证整个工作流
        assert search_results["total_results"] > 0
        assert len(memory_results) > 0
        assert plan.plan_id is not None
        
        # 获取系统统计
        knowledge_stats = knowledge_service.get_statistics()
        memory_stats = memory_system.get_memory_statistics()
        
        print("✅ 端到端工作流测试通过:")
        print(f"  - 知识库: {knowledge_stats['total_documents']} 个文档")
        print(f"  - 记忆系统: {memory_stats['total_memories']} 个记忆")
        print(f"  - 研究计划: {len(plan.tasks)} 个任务")

def create_test_document():
    """创建测试文档"""
    content = """
    # 测试文档
    
    这是一个用于测试的文档。
    
    ## 第一章
    
    这是第一章的内容。
    
    ### 1.1 小节
    
    这是第一章第一节的内容。
    
    ## 第二章
    
    这是第二章的内容。
    """
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        return f.name

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"]) 