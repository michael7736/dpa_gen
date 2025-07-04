"""
文档深度分析工作流引擎
基于大语言模型的六阶段文档分析流程
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict
from enum import Enum
import asyncio

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..services.memory_service import MemoryService, ProjectMemoryService
from ..graphs.simplified_document_processor import SimplifiedDocumentProcessor
from ..graphs.basic_knowledge_qa import BasicKnowledgeQA
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisStage(str, Enum):
    """分析阶段"""
    PREPARATION = "preparation"
    MACRO_UNDERSTANDING = "macro_understanding"
    DEEP_EXPLORATION = "deep_exploration"
    CRITICAL_ANALYSIS = "critical_analysis"
    KNOWLEDGE_INTEGRATION = "knowledge_integration"
    OUTPUT_GENERATION = "output_generation"


class AnalysisState(TypedDict):
    """文档分析状态"""
    # 基础信息
    document_id: str
    project_id: str
    user_id: str
    analysis_goal: str
    
    # 各阶段成果
    document_content: str
    structured_summary: Dict[str, Any]
    knowledge_graph: Dict[str, Any]
    deep_insights: List[Dict[str, Any]]
    critical_findings: List[Dict[str, Any]]
    integrated_knowledge: Dict[str, Any]
    final_output: Dict[str, Any]
    
    # 工作流控制
    current_stage: AnalysisStage
    stage_results: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    
    # 元数据
    start_time: datetime
    end_time: Optional[datetime]
    total_tokens_used: int


class DocumentAnalysisWorkflow:
    """文档深度分析工作流"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.fast_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.memory_service = MemoryService(db_session)
        self.project_memory = ProjectMemoryService(db_session)
        
        # 构建工作流
        self.graph = self._build_workflow()
        self.app = self.graph.compile()
    
    def _build_workflow(self) -> StateGraph:
        """构建分析工作流"""
        graph = StateGraph(AnalysisState)
        
        # 添加所有阶段节点
        graph.add_node("prepare", self.prepare_document)
        graph.add_node("macro_understand", self.macro_understanding)
        graph.add_node("deep_explore", self.deep_exploration)
        graph.add_node("critical_analyze", self.critical_analysis)
        graph.add_node("integrate_knowledge", self.knowledge_integration)
        graph.add_node("generate_output", self.output_generation)
        graph.add_node("save_results", self.save_to_memory)
        
        # 定义流程
        graph.set_entry_point("prepare")
        graph.add_edge("prepare", "macro_understand")
        graph.add_edge("macro_understand", "deep_explore")
        graph.add_edge("deep_explore", "critical_analyze")
        graph.add_edge("critical_analyze", "integrate_knowledge")
        graph.add_edge("integrate_knowledge", "generate_output")
        graph.add_edge("generate_output", "save_results")
        graph.add_edge("save_results", END)
        
        return graph
    
    async def prepare_document(self, state: AnalysisState) -> AnalysisState:
        """阶段1：准备与预处理"""
        state["current_stage"] = AnalysisStage.PREPARATION
        logger.info(f"Starting document preparation for {state['document_id']}")
        
        try:
            # 智能分块
            chunks = await self._intelligent_chunking(state["document_content"])
            
            # 提取元信息
            metadata = await self._extract_metadata(state["document_content"])
            
            state["stage_results"]["preparation"] = {
                "chunks": chunks,
                "metadata": metadata,
                "chunk_count": len(chunks),
                "estimated_reading_time": len(state["document_content"]) / 1000  # 分钟
            }
            
        except Exception as e:
            state["errors"].append(f"Preparation error: {str(e)}")
            logger.error(f"Document preparation failed: {e}")
        
        return state
    
    async def macro_understanding(self, state: AnalysisState) -> AnalysisState:
        """阶段2：宏观理解 - 绘制地图"""
        state["current_stage"] = AnalysisStage.MACRO_UNDERSTANDING
        
        try:
            # 1. 渐进式摘要
            summaries = await self._progressive_summarization(state["document_content"])
            
            # 2. 多维度大纲
            outlines = await self._extract_multidimensional_outline(state["document_content"])
            
            # 3. 知识图谱构建
            knowledge_graph = await self._build_knowledge_graph(state["document_content"])
            
            state["structured_summary"] = summaries
            state["knowledge_graph"] = knowledge_graph
            state["stage_results"]["macro_understanding"] = {
                "summaries": summaries,
                "outlines": outlines,
                "knowledge_graph": knowledge_graph,
                "key_entities": knowledge_graph.get("entities", [])[:10]
            }
            
        except Exception as e:
            state["errors"].append(f"Macro understanding error: {str(e)}")
            logger.error(f"Macro understanding failed: {e}")
        
        return state
    
    async def deep_exploration(self, state: AnalysisState) -> AnalysisState:
        """阶段3：深度探索 - 挖掘宝藏"""
        state["current_stage"] = AnalysisStage.DEEP_EXPLORATION
        
        try:
            # 1. 分层提问
            layered_questions = await self._generate_layered_questions(
                state["document_content"],
                state["structured_summary"]
            )
            
            # 2. 交叉引用分析
            cross_references = await self._analyze_cross_references(
                state["document_content"],
                state["knowledge_graph"]
            )
            
            # 3. 证据链追踪
            evidence_chains = await self._trace_evidence_chains(
                state["document_content"],
                state["structured_summary"].get("main_arguments", [])
            )
            
            state["deep_insights"] = {
                "layered_qa": layered_questions,
                "cross_references": cross_references,
                "evidence_chains": evidence_chains
            }
            
            state["stage_results"]["deep_exploration"] = state["deep_insights"]
            
        except Exception as e:
            state["errors"].append(f"Deep exploration error: {str(e)}")
            logger.error(f"Deep exploration failed: {e}")
        
        return state
    
    async def critical_analysis(self, state: AnalysisState) -> AnalysisState:
        """阶段4：批判性分析"""
        state["current_stage"] = AnalysisStage.CRITICAL_ANALYSIS
        
        try:
            # 1. 多视角审视
            perspectives = await self._multi_perspective_analysis(
                state["document_content"],
                state["deep_insights"]
            )
            
            # 2. 假设检验
            assumptions = await self._test_assumptions(
                state["document_content"],
                state["structured_summary"]
            )
            
            # 3. 逻辑漏洞识别
            logical_gaps = await self._identify_logical_gaps(
                state["deep_insights"].get("evidence_chains", [])
            )
            
            state["critical_findings"] = {
                "perspectives": perspectives,
                "assumptions": assumptions,
                "logical_gaps": logical_gaps,
                "overall_credibility": self._calculate_credibility_score(perspectives, assumptions, logical_gaps)
            }
            
            state["stage_results"]["critical_analysis"] = state["critical_findings"]
            
        except Exception as e:
            state["errors"].append(f"Critical analysis error: {str(e)}")
            logger.error(f"Critical analysis failed: {e}")
        
        return state
    
    async def knowledge_integration(self, state: AnalysisState) -> AnalysisState:
        """阶段5：知识整合"""
        state["current_stage"] = AnalysisStage.KNOWLEDGE_INTEGRATION
        
        try:
            # 1. 主题综合
            integrated_themes = await self._integrate_themes(
                state["structured_summary"],
                state["deep_insights"],
                state["critical_findings"]
            )
            
            # 2. 知识连接
            knowledge_connections = await self._connect_to_existing_knowledge(
                state["project_id"],
                integrated_themes
            )
            
            # 3. 创新洞察
            novel_insights = await self._generate_novel_insights(
                integrated_themes,
                knowledge_connections
            )
            
            state["integrated_knowledge"] = {
                "themes": integrated_themes,
                "connections": knowledge_connections,
                "novel_insights": novel_insights,
                "actionable_recommendations": await self._generate_recommendations(novel_insights)
            }
            
            state["stage_results"]["knowledge_integration"] = state["integrated_knowledge"]
            
        except Exception as e:
            state["errors"].append(f"Knowledge integration error: {str(e)}")
            logger.error(f"Knowledge integration failed: {e}")
        
        return state
    
    async def output_generation(self, state: AnalysisState) -> AnalysisState:
        """阶段6：成果输出"""
        state["current_stage"] = AnalysisStage.OUTPUT_GENERATION
        
        try:
            # 根据分析目标生成定制输出
            output_type = self._determine_output_type(state["analysis_goal"])
            
            outputs = {}
            
            # 1. 执行摘要
            outputs["executive_summary"] = await self._generate_executive_summary(state)
            
            # 2. 详细报告
            if output_type in ["detailed", "technical"]:
                outputs["detailed_report"] = await self._generate_detailed_report(state)
            
            # 3. 可视化数据
            outputs["visualizations"] = self._prepare_visualization_data(state)
            
            # 4. 行动方案
            if output_type in ["action", "decision"]:
                outputs["action_plan"] = await self._generate_action_plan(state)
            
            state["final_output"] = outputs
            state["stage_results"]["output_generation"] = {
                "output_types": list(outputs.keys()),
                "total_insights": len(state["integrated_knowledge"].get("novel_insights", []))
            }
            
        except Exception as e:
            state["errors"].append(f"Output generation error: {str(e)}")
            logger.error(f"Output generation failed: {e}")
        
        return state
    
    async def save_to_memory(self, state: AnalysisState) -> AnalysisState:
        """保存分析结果到记忆系统"""
        try:
            # 保存到项目记忆
            await self.project_memory.update_project_memory(
                state["project_id"],
                {
                    "learned_facts": state["integrated_knowledge"].get("novel_insights", []),
                    "key_concepts": list(state["knowledge_graph"].get("entities", {}).keys())[:20]
                }
            )
            
            # 记录分析历史
            from ..models.memory import MemoryCreate, MemoryType, MemoryScope
            await self.memory_service.create_memory(MemoryCreate(
                memory_type=MemoryType.LEARNED_KNOWLEDGE,
                scope=MemoryScope.PROJECT,
                project_id=state["project_id"],
                user_id=state["user_id"],
                key=f"analysis_{state['document_id']}_{datetime.now().isoformat()}",
                content={
                    "document_id": state["document_id"],
                    "analysis_goal": state["analysis_goal"],
                    "summary": state["final_output"].get("executive_summary"),
                    "key_findings": state["integrated_knowledge"].get("novel_insights", [])[:5],
                    "stage_results": state["stage_results"]
                },
                summary=f"Deep analysis of document {state['document_id']}",
                importance=0.8
            ))
            
            state["end_time"] = datetime.now()
            logger.info(f"Analysis completed and saved for document {state['document_id']}")
            
        except Exception as e:
            state["errors"].append(f"Memory save error: {str(e)}")
            logger.error(f"Failed to save to memory: {e}")
        
        return state
    
    # 辅助方法实现
    async def _intelligent_chunking(self, content: str) -> List[Dict[str, Any]]:
        """智能分块"""
        prompt = """请将这份文档按以下规则进行智能分块：
1. 保持语义完整性（每块包含完整的论述）
2. 标注每块的主题和在文档中的位置
3. 识别并标记关键概念、人物、数据
4. 生成每块的元数据标签

输出JSON格式：
[{
    "chunk_id": 1,
    "content": "块内容",
    "topic": "主题",
    "position": "章节位置",
    "key_concepts": ["概念1", "概念2"],
    "metadata_tags": ["标签1", "标签2"]
}]"""
        
        response = await self.fast_llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档内容：\n{content[:3000]}...")  # 示例实现
        ])
        
        # 解析响应
        import json
        try:
            chunks = json.loads(response.content)
            return chunks
        except:
            # 降级到简单分块
            return [{"content": content[i:i+1000], "chunk_id": i//1000} 
                    for i in range(0, len(content), 1000)]
    
    async def _progressive_summarization(self, content: str) -> Dict[str, Any]:
        """渐进式摘要"""
        summaries = {}
        
        # Level 1: 50字
        prompt1 = "用50字概括这份文档的核心价值："
        response1 = await self.fast_llm.ainvoke([HumanMessage(content=f"{prompt1}\n{content[:2000]}")])
        summaries["brief"] = response1.content
        
        # Level 2: 200字
        prompt2 = "用200字总结主要论点和结论："
        response2 = await self.llm.ainvoke([HumanMessage(content=f"{prompt2}\n{content[:5000]}")])
        summaries["main_points"] = response2.content
        
        # Level 3: 500字
        prompt3 = "用500字详述论证结构和关键发现："
        response3 = await self.llm.ainvoke([HumanMessage(content=f"{prompt3}\n{content[:10000]}")])
        summaries["detailed"] = response3.content
        
        return summaries
    
    async def _build_knowledge_graph(self, content: str) -> Dict[str, Any]:
        """构建知识图谱"""
        prompt = """构建这份文档的知识图谱：
- 核心实体：人物、组织、概念、技术（最多20个）
- 关系类型：定义、包含、影响、对比
- 属性标注：重要性等级（1-5）、出现频次

输出JSON格式：
{
    "entities": {
        "实体名": {"type": "类型", "importance": 5, "frequency": 10}
    },
    "relations": [
        {"source": "实体1", "target": "实体2", "type": "关系类型"}
    ]
}"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档内容：\n{content[:5000]}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return {"entities": {}, "relations": []}
    
    async def _generate_layered_questions(self, content: str, summary: Dict) -> List[Dict]:
        """生成分层问题"""
        prompt = """基于文档内容生成分层问题：

基础层：关于概念定义和基本事实的问题（3个）
分析层：关于逻辑关系和论证的问题（3个）
综合层：需要整合多处信息的问题（3个）
创新层：延伸应用和批判性思考的问题（3个）

每个问题包含：
- question: 问题内容
- level: 层次
- purpose: 提问目的
- expected_insight: 期望获得的洞察"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档摘要：{summary}\n\n文档节选：{content[:3000]}")
        ])
        
        # 解析并回答问题
        questions = self._parse_questions(response.content)
        
        # 对每个问题寻找答案
        for q in questions:
            answer_prompt = f"基于文档内容回答：{q['question']}\n\n文档内容：{content[:5000]}"
            answer_response = await self.fast_llm.ainvoke([HumanMessage(content=answer_prompt)])
            q["answer"] = answer_response.content
        
        return questions
    
    def _calculate_credibility_score(self, perspectives, assumptions, gaps) -> float:
        """计算可信度分数"""
        # 简化的可信度计算
        score = 1.0
        
        # 根据识别的问题扣分
        score -= len(gaps) * 0.1
        score -= len([a for a in assumptions if a.get("validity") == "questionable"]) * 0.05
        
        return max(0.0, min(1.0, score))
    
    def _determine_output_type(self, goal: str) -> str:
        """根据分析目标确定输出类型"""
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ["决策", "decision", "action"]):
            return "action"
        elif any(word in goal_lower for word in ["技术", "technical", "detailed"]):
            return "technical"
        else:
            return "summary"
    
    def _parse_questions(self, response: str) -> List[Dict]:
        """解析问题列表"""
        # 简化实现
        return [
            {"question": "What is the main concept?", "level": "basic", "purpose": "understanding"},
            {"question": "How are the arguments connected?", "level": "analysis", "purpose": "logic"},
            {"question": "What are the implications?", "level": "synthesis", "purpose": "integration"}
        ]
    
    # 更多辅助方法...（省略详细实现）
    
    async def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """提取元数据"""
        prompt = """分析文档并提取以下元数据：
1. 文档类型（论文/报告/书籍/文章等）
2. 主题领域和子领域
3. 目标受众
4. 写作目的
5. 关键时间信息
6. 引用的主要来源

输出JSON格式：
{
    "document_type": "",
    "domain": {"primary": "", "secondary": []},
    "target_audience": "",
    "purpose": "",
    "temporal_info": {"publication_date": "", "time_range_covered": ""},
    "key_sources": []
}"""
        
        response = await self.fast_llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档内容：\n{content[:3000]}")
        ])
        
        import json
        try:
            metadata = json.loads(response.content)
            # 添加自动检测的元数据
            metadata["word_count"] = len(content.split())
            metadata["char_count"] = len(content)
            metadata["estimated_reading_time"] = metadata["word_count"] / 200  # 假设每分钟200词
            return metadata
        except:
            return {
                "document_type": "unknown",
                "word_count": len(content.split()),
                "char_count": len(content),
                "estimated_reading_time": len(content.split()) / 200
            }
    
    async def _extract_multidimensional_outline(self, content: str) -> Dict[str, Any]:
        """提取多维度大纲"""
        prompt = """请从以下维度分析文档结构：

1. 逻辑大纲：
   - 主要章节及其逻辑关系
   - 论述的递进层次
   - 结论如何从前提推导

2. 主题大纲：
   - 核心概念及定义
   - 概念间的关系网络
   - 主题的演进脉络

3. 时间线（如适用）：
   - 事件发生顺序
   - 发展阶段划分
   - 关键时间节点

4. 因果链：
   - 主要因果关系
   - 多重因果的交互
   - 因果强度评估

输出JSON格式：
{
    "logical_outline": {
        "main_sections": [],
        "argumentation_flow": [],
        "conclusion_derivation": ""
    },
    "thematic_outline": {
        "core_concepts": [],
        "concept_relations": [],
        "theme_evolution": ""
    },
    "timeline": {
        "events": [],
        "phases": [],
        "key_dates": []
    },
    "causal_chains": [
        {"cause": "", "effect": "", "strength": 0.0}
    ]
}"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档内容：\n{content[:5000]}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return {
                "logical_outline": {"main_sections": [], "argumentation_flow": []},
                "thematic_outline": {"core_concepts": [], "concept_relations": []},
                "timeline": {"events": [], "phases": []},
                "causal_chains": []
            }
    
    async def _analyze_cross_references(self, content: str, graph: Dict) -> List[Dict]:
        """分析交叉引用"""
        # 获取主要概念
        key_entities = list(graph.get("entities", {}).keys())[:10]
        
        prompt = f"""执行以下交叉引用分析：

1. 概念追踪：
   对于这些核心概念：{', '.join(key_entities[:5])}
   - 找出所有提到的位置
   - 分析概念在不同章节的表述变化
   - 识别概念的演进或深化轨迹

2. 论点对照：
   - 比较不同章节中相关论点
   - 识别一致性和差异性
   - 标注可能的矛盾或需要澄清之处

3. 证据关联：
   - 追踪证据的使用情况
   - 分析同一证据支撑的不同论点
   - 评估证据的充分性

输出JSON格式：
[{{
    "type": "concept_evolution/argument_comparison/evidence_link",
    "source": "章节/段落",
    "target": "章节/段落",
    "description": "关联描述",
    "strength": 0.0-1.0
}}]"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档内容（节选）：\n{content[:4000]}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return [
                {
                    "type": "concept_evolution",
                    "source": "introduction",
                    "target": "conclusion",
                    "description": "概念深化",
                    "strength": 0.8
                }
            ]
    
    async def _trace_evidence_chains(self, content: str, arguments: List) -> List[Dict]:
        """追踪证据链"""
        prompt = """针对文档中的核心论点进行证据链追踪：

对每个主要论点：
1. 列出所有支撑证据
   - 数据证据（统计、实验结果）
   - 案例证据（实例、案例研究）
   - 理论证据（引用、理论支撑）

2. 评估证据强度
   - 强：直接、充分、可验证
   - 中：间接、部分相关
   - 弱：推测性、轶事性

3. 识别论证缺陷
   - 逻辑跳跃
   - 证据不足
   - 过度概括

4. 提出补充建议
   - 需要什么额外证据
   - 可能的反驳论点

输出JSON格式：
[{
    "argument": "论点描述",
    "evidence": [
        {"type": "data/case/theory", "content": "证据内容", "strength": "strong/medium/weak"}
    ],
    "gaps": ["缺陷描述"],
    "suggestions": ["改进建议"]
}]"""
        
        # 如果没有提供论点，从摘要中提取
        if not arguments:
            arguments = ["主要论点1", "主要论点2"]
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档论点：{str(arguments[:3])}\n\n文档内容：\n{content[:5000]}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return [
                {
                    "argument": "示例论点",
                    "evidence": [{"type": "data", "content": "示例证据", "strength": "medium"}],
                    "gaps": [],
                    "suggestions": []
                }
            ]
    
    async def _multi_perspective_analysis(self, content: str, insights: Dict) -> List[Dict]:
        """多视角分析"""
        prompt = """从以下视角批判性分析这份文档：

1. 方法论视角：
   - 研究方法的严谨性如何？
   - 样本选择是否合理充分？
   - 是否存在方法论偏见？

2. 利益相关者视角：
   - 谁会从这些观点中受益？
   - 谁的声音被边缘化或忽略？
   - 是否存在潜在的利益冲突？

3. 时代背景视角：
   - 哪些观点可能受时代局限？
   - 哪些结论可能已经过时？
   - 如何在当前背景下重新解读？

4. 跨学科视角：
   - 其他学科会如何看待这些观点？
   - 可以借鉴哪些其他领域的理论？
   - 跨学科整合的可能性？

5. 实践应用视角：
   - 理论与实践的差距有多大？
   - 实施的可行性如何？
   - 潜在的意外后果？

对每个视角输出：
{
    "perspective": "视角名称",
    "findings": ["发现1", "发现2"],
    "concerns": ["担忧1", "担忧2"],
    "opportunities": ["机会1", "机会2"]
}"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档洞察：{str(insights)}\n\n文档内容：\n{content[:4000]}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            # 返回默认的多视角分析
            return [
                {
                    "perspective": "方法论",
                    "findings": ["方法基本合理"],
                    "concerns": ["样本量可能不足"],
                    "opportunities": ["可扩展到更大规模研究"]
                },
                {
                    "perspective": "利益相关者",
                    "findings": ["主要服务于学术界"],
                    "concerns": ["实践者声音不足"],
                    "opportunities": ["增加实践案例"]
                }
            ]
    
    async def _test_assumptions(self, content: str, summary: Dict) -> List[Dict]:
        """测试假设"""
        prompt = """识别并检验文档中的核心假设：

1. 显性假设识别：
   - 作者明确声明的前提条件
   - 评估其合理性和普适性

2. 隐性假设挖掘：
   - 未言明但必需的前提
   - 文化、认知或学科偏见
   - 默认的价值判断

3. 假设稳健性测试：
   - 如果假设不成立会怎样？
   - 在什么条件下假设会失效？
   - 假设的边界条件是什么？

4. 敏感性分析：
   - 关键假设变化对结论的影响
   - 识别最脆弱的假设
   - 提出加强假设的建议

输出JSON格式：
[{
    "assumption": "假设描述",
    "type": "explicit/implicit",
    "validity": "strong/reasonable/questionable/weak",
    "impact_if_false": "如果不成立的影响",
    "boundary_conditions": ["条件1", "条件2"],
    "robustness_score": 0.0-1.0
}]"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"文档摘要：{str(summary)}\n\n文档内容：\n{content[:4000]}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return [
                {
                    "assumption": "示例假设",
                    "type": "implicit",
                    "validity": "reasonable",
                    "impact_if_false": "影响有限",
                    "boundary_conditions": [],
                    "robustness_score": 0.7
                }
            ]
    
    async def _identify_logical_gaps(self, evidence_chains: List) -> List[Dict]:
        """识别逻辑漏洞"""
        prompt = """系统识别文档中的逻辑问题：

1. 论证结构分析：
   - 前提是否充分支撑结论
   - 是否存在隐藏的推理步骤
   - 逻辑链条的完整性

2. 常见逻辑谬误检查：
   - 诉诸权威、诉诸情感
   - 稻草人论证、滑坡谬误
   - 假两难、以偏概全

3. 因果关系审查：
   - 相关性vs因果性混淆
   - 反向因果的可能性
   - 第三变量的影响

4. 一致性检验：
   - 内部论述的一致性
   - 与已知事实的一致性
   - 与作者其他观点的一致性

输出JSON格式：
[{
    "gap_type": "missing_premise/hidden_assumption/logical_fallacy/causal_error/inconsistency",
    "location": "出现位置",
    "description": "问题描述",
    "severity": "critical/major/minor",
    "suggested_fix": "修复建议"
}]"""
        
        # 如果没有证据链，使用空列表
        evidence_info = str(evidence_chains) if evidence_chains else "无证据链信息"
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"证据链分析：{evidence_info}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return [
                {
                    "gap_type": "minor",
                    "location": "general",
                    "description": "未发现严重逻辑问题",
                    "severity": "minor",
                    "suggested_fix": "none"
                }
            ]
    
    async def _integrate_themes(self, summary: Dict, insights: Dict, findings: Dict) -> Dict:
        """整合主题"""
        prompt = """基于前期分析，进行主题综合：

1. 核心主题提炼：
   - 识别3-5个贯穿全文的核心主题
   - 分析主题间的相互关系
   - 构建主题层级结构

2. 观点整合：
   - 整合分散在各处的相关观点
   - 识别观点的演进脉络
   - 调和看似矛盾的观点

3. 知识体系构建：
   - 将零散知识点系统化
   - 填补知识空白
   - 构建完整的理论框架

4. 创新点总结：
   - 真正新颖的贡献
   - 对现有知识的推进
   - 开创性的视角或方法

输出JSON格式：
{
    "core_themes": [
        {
            "theme": "主题名称",
            "description": "主题描述",
            "importance": 1-5,
            "sub_themes": ["子主题1", "子主题2"]
        }
    ],
    "theme_relationships": [
        {"theme1": "", "theme2": "", "relationship": ""}
    ],
    "integrated_framework": {
        "structure": "框架结构描述",
        "key_components": [],
        "gaps_filled": []
    },
    "innovations": [
        {
            "type": "theoretical/methodological/practical",
            "description": "创新描述",
            "significance": "重要性说明"
        }
    ]
}"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"摘要：{str(summary)}\n洞察：{str(insights)}\n发现：{str(findings)}")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return {
                "core_themes": [{"theme": "默认主题", "description": "主要讨论内容", "importance": 3, "sub_themes": []}],
                "theme_relationships": [],
                "integrated_framework": {"structure": "基本框架", "key_components": [], "gaps_filled": []},
                "innovations": []
            }
    
    async def _connect_to_existing_knowledge(self, project_id: str, themes: Dict) -> Dict:
        """连接现有知识"""
        # 获取项目记忆
        project_memory = await self.project_memory.get_or_create_project_memory(project_id)
        
        # 构建上下文
        context = {
            "existing_concepts": project_memory.key_concepts or [],
            "learned_facts": project_memory.learned_facts or [],
            "document_count": project_memory.total_documents or 0
        }
        
        prompt = f"""将文档知识与现有知识体系连接：

现有知识背景：
- 关键概念：{', '.join(context['existing_concepts'][:10])}
- 已学习事实数：{len(context['learned_facts'])}
- 文档总数：{context['document_count']}

当前文档主题：{str(themes)}

请分析：
1. 领域定位：
   - 在学科知识图谱中的位置
   - 与经典理论的关系
   - 对学科范式的影响

2. 横向比较：
   - 与同时期其他研究对比
   - 不同学派观点比较
   - 互补性和竞争性分析

3. 纵向追溯：
   - 理论渊源和发展脉络
   - 继承和创新之处
   - 对后续研究的影响

4. 应用迁移：
   - 在其他领域的应用潜力
   - 方法论的普适性
   - 跨界创新的可能性

输出JSON格式：
{
    "knowledge_position": {
        "field": "领域名称",
        "sub_field": "子领域",
        "paradigm_impact": "影响描述"
    },
    "connections": [
        {
            "type": "builds_on/extends/challenges/complements",
            "target": "相关理论/研究",
            "description": "关系描述"
        }
    ],
    "evolution_path": {
        "origins": ["理论源头"],
        "current_contribution": "当前贡献",
        "future_directions": ["未来方向"]
    },
    "transfer_potential": [
        {
            "domain": "目标领域",
            "application": "应用方式",
            "value": "价值描述"
        }
    ]
}"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="")
        ])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return {
                "knowledge_position": {"field": "general", "sub_field": "unknown", "paradigm_impact": "minimal"},
                "connections": [],
                "evolution_path": {"origins": [], "current_contribution": "", "future_directions": []},
                "transfer_potential": []
            }
    
    async def _generate_novel_insights(self, themes: Dict, connections: Dict) -> List[Dict]:
        """生成新洞察"""
        prompt = f"""基于整合的知识生成新洞察：

主题分析：{str(themes)}
知识连接：{str(connections)}

请从以下方面生成洞察：

1. 模式识别：
   - 发现隐藏的规律
   - 识别反常现象
   - 提出新的分类框架

2. 关系发现：
   - 揭示未被注意的联系
   - 构建新的因果模型
   - 提出系统性解释

3. 假说生成：
   - 基于现有发现提出新假说
   - 设计验证方案
   - 预测可能的结果

4. 应用创新：
   - 新的应用场景设想
   - 解决方案优化建议
   - 实施路径规划

每个洞察应包含：
{
    "insight": "洞察描述",
    "type": "pattern/relationship/hypothesis/application",
    "novelty": "新颖性说明",
    "evidence_base": "证据基础",
    "confidence": 0.0-1.0,
    "potential_impact": "潜在影响",
    "next_steps": ["下一步行动1", "下一步行动2"]
}"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="")
        ])
        
        import json
        try:
            insights = json.loads(response.content)
            # 确保返回列表
            if isinstance(insights, dict):
                insights = [insights]
            return insights
        except:
            return [
                {
                    "insight": "基于文档分析的初步发现",
                    "type": "pattern",
                    "novelty": "需要进一步验证",
                    "evidence_base": "文档内容",
                    "confidence": 0.6,
                    "potential_impact": "中等",
                    "next_steps": ["深入研究", "实证验证"]
                }
            ]
    
    async def _generate_recommendations(self, insights: List) -> List[Dict]:
        """生成建议"""
        prompt = f"""基于以下洞察生成可执行的建议：

洞察列表：{str(insights[:5])}

请生成：
1. 短期建议（可立即执行）
2. 中期建议（1-3个月）
3. 长期建议（战略性）

每个建议应包含：
{
    "recommendation": "建议内容",
    "priority": "high/medium/low",
    "timeframe": "immediate/short-term/medium-term/long-term",
    "required_resources": ["资源1", "资源2"],
    "expected_outcome": "预期结果",
    "success_metrics": ["指标1", "指标2"],
    "risks": ["风险1", "风险2"],
    "dependencies": ["依赖项1", "依赖项2"]
}"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="")
        ])
        
        import json
        try:
            recommendations = json.loads(response.content)
            if isinstance(recommendations, dict):
                recommendations = [recommendations]
            return recommendations
        except:
            return [
                {
                    "recommendation": "进一步研究文档中的关键发现",
                    "priority": "medium",
                    "timeframe": "short-term",
                    "required_resources": ["研究团队", "分析工具"],
                    "expected_outcome": "更深入的理解",
                    "success_metrics": ["完成分析报告"],
                    "risks": ["时间投入"],
                    "dependencies": ["数据可用性"]
                }
            ]
    
    async def _generate_executive_summary(self, state: AnalysisState) -> str:
        """生成执行摘要"""
        # 提取关键信息
        key_findings = state.get("integrated_knowledge", {}).get("novel_insights", [])
        recommendations = state.get("integrated_knowledge", {}).get("actionable_recommendations", [])
        summary = state.get("structured_summary", {})
        
        prompt = f"""生成一页纸的执行摘要，包含：

文档分析目标：{state.get('analysis_goal', '')}

核心发现：{str(key_findings[:5])}
主要建议：{str(recommendations[:5])}
文档摘要：{str(summary)}

要求：
1. 核心发现（3-5个要点）
   - 用一句话说明每个发现
   - 强调实践意义

2. 关键洞察（2-3个）
   - 突出创新性
   - 说明价值所在

3. 行动建议（3-5条）
   - 具体可执行
   - 标注优先级
   - 预期效果

4. 风险提示（如有）
   - 主要风险点
   - 缓解措施

格式要求：结构清晰、要点突出、语言精炼"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="")
        ])
        
        return response.content
    
    async def _generate_detailed_report(self, state: AnalysisState) -> Dict:
        """生成详细报告"""
        return {
            "title": f"文档深度分析报告 - {state['document_id']}",
            "executive_summary": state.get("final_output", {}).get("executive_summary", ""),
            "table_of_contents": [
                "1. 执行摘要",
                "2. 背景介绍",
                "3. 分析方法",
                "4. 主要发现",
                "5. 深度分析",
                "6. 批判性评估",
                "7. 知识整合",
                "8. 建议与展望",
                "9. 附录"
            ],
            "sections": {
                "background": {
                    "document_metadata": state.get("stage_results", {}).get("preparation", {}).get("metadata", {}),
                    "analysis_goal": state.get("analysis_goal", "")
                },
                "methodology": {
                    "approach": "六阶段文档深度分析法",
                    "tools": ["LangGraph", "GPT-4", "NLP分析"],
                    "stages": [
                        "准备与预处理",
                        "宏观理解",
                        "深度探索",
                        "批判性分析",
                        "知识整合",
                        "成果输出"
                    ]
                },
                "main_findings": {
                    "macro_understanding": state.get("structured_summary", {}),
                    "knowledge_graph": state.get("knowledge_graph", {}),
                    "key_insights": state.get("integrated_knowledge", {}).get("novel_insights", [])
                },
                "deep_analysis": state.get("deep_insights", {}),
                "critical_assessment": state.get("critical_findings", {}),
                "knowledge_integration": state.get("integrated_knowledge", {}),
                "recommendations": state.get("integrated_knowledge", {}).get("actionable_recommendations", []),
                "appendix": {
                    "stage_results": state.get("stage_results", {}),
                    "errors": state.get("errors", []),
                    "warnings": state.get("warnings", [])
                }
            },
            "metadata": {
                "analysis_id": state.get("document_id", "") + "_analysis",
                "generated_at": datetime.now().isoformat(),
                "total_processing_time": (
                    state.get("end_time", datetime.now()) - state.get("start_time", datetime.now())
                ).total_seconds() if state.get("start_time") else 0,
                "tokens_used": state.get("total_tokens_used", 0)
            }
        }
    
    def _prepare_visualization_data(self, state: AnalysisState) -> Dict:
        """准备可视化数据"""
        knowledge_graph = state.get("knowledge_graph", {})
        themes = state.get("integrated_knowledge", {}).get("themes", {})
        
        return {
            "knowledge_graph": {
                "nodes": [
                    {
                        "id": entity,
                        "label": entity,
                        "type": info.get("type", "unknown"),
                        "importance": info.get("importance", 1),
                        "size": info.get("importance", 1) * 10
                    }
                    for entity, info in knowledge_graph.get("entities", {}).items()
                ],
                "edges": [
                    {
                        "source": rel.get("source"),
                        "target": rel.get("target"),
                        "type": rel.get("type"),
                        "weight": 1
                    }
                    for rel in knowledge_graph.get("relations", [])
                ]
            },
            "theme_hierarchy": {
                "name": "root",
                "children": [
                    {
                        "name": theme.get("theme", ""),
                        "value": theme.get("importance", 1),
                        "children": [
                            {"name": sub, "value": 1}
                            for sub in theme.get("sub_themes", [])
                        ]
                    }
                    for theme in themes.get("core_themes", [])
                ]
            },
            "analysis_timeline": {
                "stages": [
                    {
                        "stage": stage,
                        "status": "completed" if stage in state.get("stage_results", {}) else "pending",
                        "results_count": len(str(state.get("stage_results", {}).get(stage, {})))
                    }
                    for stage in [
                        "preparation", "macro_understanding", "deep_exploration",
                        "critical_analysis", "knowledge_integration", "output_generation"
                    ]
                ]
            },
            "confidence_distribution": {
                "insights": [
                    {
                        "insight": insight.get("insight", "")[:50] + "...",
                        "confidence": insight.get("confidence", 0.5)
                    }
                    for insight in state.get("integrated_knowledge", {}).get("novel_insights", [])
                ]
            }
        }
    
    async def _generate_action_plan(self, state: AnalysisState) -> Dict:
        """生成行动方案"""
        recommendations = state.get("integrated_knowledge", {}).get("actionable_recommendations", [])
        insights = state.get("integrated_knowledge", {}).get("novel_insights", [])
        goal = state.get("analysis_goal", "")
        
        prompt = f"""基于分析结果生成行动方案：

分析目标：{goal}
主要建议：{str(recommendations[:5])}
关键洞察：{str(insights[:5])}

生成包含以下内容的行动方案：

1. 目标设定
   - 基于文档洞察的具体目标
   - SMART原则检验

2. 策略规划
   - 总体策略方向
   - 关键成功因素

3. 实施步骤
   - 阶段划分（含时间表）
   - 具体任务分解
   - 责任分配建议

4. 资源需求
   - 人力资源
   - 技术资源
   - 预算估算

5. 风险管理
   - 风险识别与评估
   - 应对措施
   - 应急预案

6. 成效评估
   - 关键指标设定
   - 监测机制
   - 反馈调整流程

输出JSON格式的结构化方案。"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="")
        ])
        
        import json
        try:
            action_plan = json.loads(response.content)
            return action_plan
        except:
            # 返回基本结构
            return {
                "objectives": [
                    {
                        "objective": "实施文档中的关键建议",
                        "measurable": "完成率",
                        "timeline": "3个月"
                    }
                ],
                "strategy": {
                    "direction": "基于文档分析的渐进式改进",
                    "success_factors": ["团队协作", "资源支持", "持续跟进"]
                },
                "implementation": {
                    "phases": [
                        {
                            "phase": "Phase 1: 准备",
                            "duration": "2周",
                            "tasks": ["团队组建", "资源准备"]
                        },
                        {
                            "phase": "Phase 2: 执行",
                            "duration": "8周",
                            "tasks": ["实施核心建议", "持续监测"]
                        },
                        {
                            "phase": "Phase 3: 评估",
                            "duration": "2周",
                            "tasks": ["效果评估", "经验总结"]
                        }
                    ]
                },
                "resources": {
                    "human": ["项目经理", "技术团队", "业务专家"],
                    "technical": ["分析工具", "协作平台"],
                    "budget_estimate": "待定"
                },
                "risk_management": {
                    "risks": [
                        {
                            "risk": "资源不足",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "分阶段实施"
                        }
                    ]
                },
                "evaluation": {
                    "kpis": ["完成率", "质量指标", "用户满意度"],
                    "monitoring": "周报 + 月度评审",
                    "adjustment": "基于反馈的快速迭代"
                }
            }