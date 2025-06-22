"""
基于LangGraph的研究规划智能体
参考OpenAI DeepResearch工作流，实现智能研究规划和执行
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, TypedDict
from uuid import UUID, uuid4
from datetime import datetime

from langgraph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config.settings import get_settings
from ..database.neo4j_client import get_neo4j_manager
from ..database.qdrant_client import get_qdrant_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ResearchPlanningState(TypedDict):
    """研究规划状态"""
    # 输入信息
    project_id: str
    research_topic: str
    research_objectives: List[str]
    domain_context: Optional[str]
    existing_knowledge: Optional[Dict[str, Any]]
    
    # 规划过程数据
    research_questions: Optional[List[Dict[str, Any]]]
    search_strategies: Optional[List[Dict[str, Any]]]
    information_gaps: Optional[List[Dict[str, Any]]]
    research_plan: Optional[Dict[str, Any]]
    execution_timeline: Optional[Dict[str, Any]]
    
    # 执行过程数据
    current_phase: str
    completed_tasks: List[Dict[str, Any]]
    collected_information: List[Dict[str, Any]]
    synthesized_insights: Optional[Dict[str, Any]]
    
    # 状态和结果
    planning_status: str
    current_step: str
    error_message: Optional[str]
    warnings: List[str]
    result: Optional[Dict[str, Any]]


class ResearchPlanningAgent:
    """基于LangGraph的研究规划智能体"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.ai_model.default_chat_model,
            temperature=0.3
        )
        self.neo4j_manager = get_neo4j_manager()
        self.qdrant_manager = get_qdrant_manager()
        self.graph = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """构建研究规划工作流"""
        workflow = StateGraph(ResearchPlanningState)
        
        # 添加规划节点
        workflow.add_node("analyze_research_topic", self.analyze_research_topic)
        workflow.add_node("generate_research_questions", self.generate_research_questions)
        workflow.add_node("identify_information_gaps", self.identify_information_gaps)
        workflow.add_node("design_search_strategies", self.design_search_strategies)
        workflow.add_node("create_research_plan", self.create_research_plan)
        workflow.add_node("execute_information_gathering", self.execute_information_gathering)
        workflow.add_node("synthesize_findings", self.synthesize_findings)
        workflow.add_node("generate_insights", self.generate_insights)
        workflow.add_node("finalize_research", self.finalize_research)
        workflow.add_node("handle_error", self.handle_error)
        
        # 定义工作流路径
        workflow.set_entry_point("analyze_research_topic")
        
        # 条件路由
        workflow.add_conditional_edges(
            "analyze_research_topic",
            self._should_continue_after_analysis,
            {
                "continue": "generate_research_questions",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("generate_research_questions", "identify_information_gaps")
        workflow.add_edge("identify_information_gaps", "design_search_strategies")
        workflow.add_edge("design_search_strategies", "create_research_plan")
        
        workflow.add_conditional_edges(
            "create_research_plan",
            self._should_execute_plan,
            {
                "execute": "execute_information_gathering",
                "plan_only": "finalize_research",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("execute_information_gathering", "synthesize_findings")
        workflow.add_edge("synthesize_findings", "generate_insights")
        workflow.add_edge("generate_insights", "finalize_research")
        workflow.add_edge("finalize_research", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _should_continue_after_analysis(self, state: ResearchPlanningState) -> str:
        """分析后的条件判断"""
        if state["planning_status"] == "error":
            return "error"
        return "continue"
    
    def _should_execute_plan(self, state: ResearchPlanningState) -> str:
        """是否执行研究计划"""
        if state["planning_status"] == "error":
            return "error"
        
        # 检查是否需要立即执行
        research_plan = state.get("research_plan", {})
        if research_plan.get("auto_execute", False):
            return "execute"
        else:
            return "plan_only"
    
    async def analyze_research_topic(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """分析研究主题"""
        state["current_step"] = "analyze_research_topic"
        
        try:
            logger.info(f"开始分析研究主题: {state['research_topic']}")
            
            # 构建分析提示
            analysis_prompt = f"""
            作为一个专业的研究规划助手，请深入分析以下研究主题：

            研究主题：{state['research_topic']}
            研究目标：{', '.join(state['research_objectives'])}
            领域背景：{state.get('domain_context', '未提供')}

            请从以下几个维度进行分析：
            1. 主题复杂度和研究范围
            2. 关键概念和术语识别
            3. 潜在的研究挑战和难点
            4. 相关研究领域和交叉学科
            5. 预期的研究深度和广度

            请以JSON格式返回分析结果。
            """
            
            messages = [
                SystemMessage(content="你是一个专业的研究规划助手，擅长分析研究主题并制定详细的研究计划。"),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析响应（简化版本，实际应该有更robust的解析）
            try:
                analysis_result = json.loads(response.content)
            except:
                # 如果JSON解析失败，创建基本结构
                analysis_result = {
                    "complexity_level": "medium",
                    "key_concepts": [state['research_topic']],
                    "challenges": ["需要进一步细化研究范围"],
                    "related_fields": ["相关领域待确定"],
                    "research_scope": "medium"
                }
            
            state["existing_knowledge"] = analysis_result
            state["planning_status"] = "analyzed"
            
            logger.info(f"研究主题分析完成: {analysis_result}")
            
        except Exception as e:
            state["error_message"] = f"研究主题分析失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"研究主题分析失败: {e}")
            
        return state
    
    async def generate_research_questions(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """生成研究问题"""
        state["current_step"] = "generate_research_questions"
        
        try:
            logger.info("开始生成研究问题")
            
            # 构建问题生成提示
            questions_prompt = f"""
            基于以下研究主题和分析结果，生成具体的研究问题：

            研究主题：{state['research_topic']}
            研究目标：{', '.join(state['research_objectives'])}
            分析结果：{json.dumps(state.get('existing_knowledge', {}), ensure_ascii=False)}

            请生成以下类型的研究问题：
            1. 核心研究问题（2-3个）：直接关联研究目标的主要问题
            2. 子问题（3-5个）：支撑核心问题的具体细分问题
            3. 探索性问题（2-3个）：可能发现新见解的开放性问题

            每个问题都应该包含：
            - 问题描述
            - 问题类型（核心/子问题/探索性）
            - 预期答案类型（定性/定量/混合）
            - 重要性级别（高/中/低）
            - 预估研究难度（简单/中等/困难）

            请以JSON格式返回。
            """
            
            messages = [
                SystemMessage(content="你是一个专业的研究规划助手，擅长将研究主题分解为具体可执行的研究问题。"),
                HumanMessage(content=questions_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                research_questions = json.loads(response.content)
            except:
                # 如果JSON解析失败，创建基本结构
                research_questions = [
                    {
                        "question": f"关于{state['research_topic']}的核心问题是什么？",
                        "type": "核心",
                        "answer_type": "混合",
                        "importance": "高",
                        "difficulty": "中等"
                    }
                ]
            
            state["research_questions"] = research_questions
            state["planning_status"] = "questions_generated"
            
            logger.info(f"研究问题生成完成: {len(research_questions)} 个问题")
            
        except Exception as e:
            state["error_message"] = f"研究问题生成失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"研究问题生成失败: {e}")
            
        return state
    
    async def identify_information_gaps(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """识别信息缺口"""
        state["current_step"] = "identify_information_gaps"
        
        try:
            logger.info("开始识别信息缺口")
            
            # 查询现有知识库
            existing_docs = await self._search_existing_knowledge(
                state["project_id"], 
                state["research_topic"]
            )
            
            # 分析信息缺口
            gaps_prompt = f"""
            基于以下研究问题和现有知识，识别信息缺口：

            研究问题：{json.dumps(state.get('research_questions', []), ensure_ascii=False)}
            现有知识文档数量：{len(existing_docs)}
            现有知识概要：{self._summarize_existing_docs(existing_docs)}

            请识别以下类型的信息缺口：
            1. 关键概念定义缺口
            2. 实证数据缺口
            3. 理论框架缺口
            4. 最新进展缺口
            5. 对比分析缺口

            对每个缺口，请提供：
            - 缺口描述
            - 缺口类型
            - 影响程度（高/中/低）
            - 填补难度（简单/中等/困难）
            - 推荐信息源类型

            请以JSON格式返回。
            """
            
            messages = [
                SystemMessage(content="你是一个专业的信息分析师，擅长识别研究中的知识缺口。"),
                HumanMessage(content=gaps_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                information_gaps = json.loads(response.content)
            except:
                information_gaps = [
                    {
                        "description": f"关于{state['research_topic']}的基础信息需要补充",
                        "type": "基础知识缺口",
                        "impact": "中",
                        "difficulty": "中等",
                        "recommended_sources": ["学术论文", "权威报告"]
                    }
                ]
            
            state["information_gaps"] = information_gaps
            state["planning_status"] = "gaps_identified"
            
            logger.info(f"信息缺口识别完成: {len(information_gaps)} 个缺口")
            
        except Exception as e:
            state["error_message"] = f"信息缺口识别失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"信息缺口识别失败: {e}")
            
        return state
    
    async def design_search_strategies(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """设计搜索策略"""
        state["current_step"] = "design_search_strategies"
        
        try:
            logger.info("开始设计搜索策略")
            
            # 构建搜索策略设计提示
            strategy_prompt = f"""
            基于以下研究问题和信息缺口，设计具体的搜索策略：

            研究问题：{json.dumps(state.get('research_questions', []), ensure_ascii=False)}
            信息缺口：{json.dumps(state.get('information_gaps', []), ensure_ascii=False)}

            请为每个主要研究问题设计搜索策略，包括：
            1. 关键词组合（中英文）
            2. 搜索数据库/平台选择
            3. 搜索过滤条件（时间范围、语言、文档类型等）
            4. 搜索深度（初步/深入/全面）
            5. 预期结果数量范围

            特别考虑以下搜索源：
            - 学术数据库（如arXiv、PubMed、Google Scholar）
            - 行业报告和白皮书
            - 政府和机构发布的官方文档
            - 技术博客和专业网站
            - 专利数据库

            请以JSON格式返回搜索策略列表。
            """
            
            messages = [
                SystemMessage(content="你是一个专业的信息检索专家，擅长设计高效的搜索策略。"),
                HumanMessage(content=strategy_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                search_strategies = json.loads(response.content)
            except:
                search_strategies = [
                    {
                        "target_question": state['research_topic'],
                        "keywords": [state['research_topic']],
                        "databases": ["arXiv", "Google Scholar"],
                        "filters": {"time_range": "recent_5_years"},
                        "search_depth": "深入",
                        "expected_results": "50-100"
                    }
                ]
            
            state["search_strategies"] = search_strategies
            state["planning_status"] = "strategies_designed"
            
            logger.info(f"搜索策略设计完成: {len(search_strategies)} 个策略")
            
        except Exception as e:
            state["error_message"] = f"搜索策略设计失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"搜索策略设计失败: {e}")
            
        return state
    
    async def create_research_plan(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """创建研究计划"""
        state["current_step"] = "create_research_plan"
        
        try:
            logger.info("开始创建研究计划")
            
            # 构建研究计划
            research_plan = {
                "project_id": state["project_id"],
                "research_topic": state["research_topic"],
                "objectives": state["research_objectives"],
                "research_questions": state.get("research_questions", []),
                "information_gaps": state.get("information_gaps", []),
                "search_strategies": state.get("search_strategies", []),
                "phases": self._create_research_phases(state),
                "timeline": self._create_timeline(state),
                "resources_needed": self._identify_resources(state),
                "success_criteria": self._define_success_criteria(state),
                "risk_assessment": self._assess_risks(state),
                "auto_execute": False  # 默认不自动执行
            }
            
            state["research_plan"] = research_plan
            state["planning_status"] = "plan_created"
            
            logger.info(f"研究计划创建完成: {len(research_plan['phases'])} 个阶段")
            
        except Exception as e:
            state["error_message"] = f"研究计划创建失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"研究计划创建失败: {e}")
            
        return state
    
    async def execute_information_gathering(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """执行信息收集"""
        state["current_step"] = "execute_information_gathering"
        
        try:
            logger.info("开始执行信息收集")
            
            search_strategies = state.get("search_strategies", [])
            collected_info = []
            
            # 执行每个搜索策略
            for strategy in search_strategies:
                try:
                    # 这里应该集成实际的搜索API
                    # 目前使用模拟数据
                    search_results = await self._execute_search_strategy(strategy)
                    collected_info.extend(search_results)
                    
                except Exception as e:
                    logger.warning(f"搜索策略执行失败: {e}")
                    state["warnings"].append(f"搜索策略执行失败: {str(e)}")
            
            state["collected_information"] = collected_info
            state["planning_status"] = "information_gathered"
            
            logger.info(f"信息收集完成: {len(collected_info)} 条信息")
            
        except Exception as e:
            state["error_message"] = f"信息收集失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"信息收集失败: {e}")
            
        return state
    
    async def synthesize_findings(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """综合研究发现"""
        state["current_step"] = "synthesize_findings"
        
        try:
            logger.info("开始综合研究发现")
            
            collected_info = state.get("collected_information", [])
            research_questions = state.get("research_questions", [])
            
            # 构建综合分析提示
            synthesis_prompt = f"""
            基于收集到的信息，请综合分析并回答研究问题：

            研究问题：{json.dumps(research_questions, ensure_ascii=False)}
            收集信息数量：{len(collected_info)}
            信息概要：{self._summarize_collected_info(collected_info)}

            请进行以下分析：
            1. 对每个研究问题的回答和支撑证据
            2. 发现的关键模式和趋势
            3. 不同信息源之间的一致性和矛盾
            4. 仍然存在的知识缺口
            5. 意外发现和新的研究方向

            请以结构化的JSON格式返回综合分析结果。
            """
            
            messages = [
                SystemMessage(content="你是一个专业的研究分析师，擅长综合多源信息并提取关键洞察。"),
                HumanMessage(content=synthesis_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                synthesized_insights = json.loads(response.content)
            except:
                synthesized_insights = {
                    "question_answers": [],
                    "key_patterns": [],
                    "consistency_analysis": {},
                    "remaining_gaps": [],
                    "unexpected_findings": []
                }
            
            state["synthesized_insights"] = synthesized_insights
            state["planning_status"] = "findings_synthesized"
            
            logger.info("研究发现综合完成")
            
        except Exception as e:
            state["error_message"] = f"研究发现综合失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"研究发现综合失败: {e}")
            
        return state
    
    async def generate_insights(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """生成研究洞察"""
        state["current_step"] = "generate_insights"
        
        try:
            logger.info("开始生成研究洞察")
            
            synthesized_insights = state.get("synthesized_insights", {})
            research_objectives = state["research_objectives"]
            
            # 构建洞察生成提示
            insights_prompt = f"""
            基于综合分析结果，生成深度研究洞察：

            研究目标：{', '.join(research_objectives)}
            综合分析：{json.dumps(synthesized_insights, ensure_ascii=False)}

            请生成以下类型的洞察：
            1. 核心发现和结论
            2. 理论贡献和创新点
            3. 实际应用价值和建议
            4. 未来研究方向
            5. 方法论反思和改进

            每个洞察应包含：
            - 洞察描述
            - 支撑证据
            - 置信度评估
            - 影响范围
            - 应用建议

            请以JSON格式返回洞察列表。
            """
            
            messages = [
                SystemMessage(content="你是一个资深研究专家，擅长从研究发现中提取深度洞察和价值。"),
                HumanMessage(content=insights_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            try:
                research_insights = json.loads(response.content)
            except:
                research_insights = [
                    {
                        "type": "核心发现",
                        "description": f"关于{state['research_topic']}的关键洞察",
                        "evidence": "基于综合分析",
                        "confidence": "中等",
                        "impact": "中等",
                        "recommendations": ["需要进一步验证"]
                    }
                ]
            
            # 更新综合洞察
            state["synthesized_insights"]["research_insights"] = research_insights
            state["planning_status"] = "insights_generated"
            
            logger.info(f"研究洞察生成完成: {len(research_insights)} 个洞察")
            
        except Exception as e:
            state["error_message"] = f"研究洞察生成失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"研究洞察生成失败: {e}")
            
        return state
    
    async def finalize_research(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """完成研究"""
        state["current_step"] = "finalize_research"
        
        try:
            # 构建最终结果
            result = {
                "project_id": state["project_id"],
                "research_topic": state["research_topic"],
                "planning_status": state["planning_status"],
                "research_plan": state.get("research_plan", {}),
                "research_questions": state.get("research_questions", []),
                "information_gaps": state.get("information_gaps", []),
                "search_strategies": state.get("search_strategies", []),
                "collected_information_count": len(state.get("collected_information", [])),
                "synthesized_insights": state.get("synthesized_insights", {}),
                "warnings": state.get("warnings", []),
                "completed_phases": state.get("completed_tasks", [])
            }
            
            state["result"] = result
            state["planning_status"] = "completed"
            
            logger.info(f"研究规划完成: {state['research_topic']}")
            
        except Exception as e:
            state["error_message"] = f"研究完成阶段失败: {str(e)}"
            state["planning_status"] = "error"
            logger.error(f"研究完成阶段失败: {e}")
            
        return state
    
    async def handle_error(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """处理错误"""
        state["current_step"] = "handle_error"
        
        error_result = {
            "project_id": state["project_id"],
            "research_topic": state["research_topic"],
            "planning_status": "failed",
            "error_message": state.get("error_message", "未知错误"),
            "failed_step": state.get("current_step", "unknown"),
            "warnings": state.get("warnings", [])
        }
        
        state["result"] = error_result
        state["planning_status"] = "failed"
        
        logger.error(f"研究规划失败: {state['research_topic']}, 错误: {state.get('error_message')}")
        
        return state
    
    # 辅助方法
    async def _search_existing_knowledge(self, project_id: str, topic: str) -> List[Dict[str, Any]]:
        """搜索现有知识"""
        try:
            # 这里应该实现实际的知识库搜索
            # 目前返回模拟数据
            return []
        except Exception as e:
            logger.error(f"搜索现有知识失败: {e}")
            return []
    
    def _summarize_existing_docs(self, docs: List[Dict[str, Any]]) -> str:
        """总结现有文档"""
        if not docs:
            return "暂无相关文档"
        return f"找到{len(docs)}个相关文档，涵盖基础概念和部分应用案例"
    
    def _summarize_collected_info(self, info_list: List[Dict[str, Any]]) -> str:
        """总结收集的信息"""
        if not info_list:
            return "暂无收集信息"
        return f"收集了{len(info_list)}条信息，包括学术论文、技术报告等"
    
    def _create_research_phases(self, state: ResearchPlanningState) -> List[Dict[str, Any]]:
        """创建研究阶段"""
        phases = [
            {
                "phase_name": "文献调研阶段",
                "description": "收集和分析相关文献",
                "duration_days": 7,
                "tasks": ["关键词搜索", "文献筛选", "文献分析"],
                "deliverables": ["文献综述", "知识图谱"]
            },
            {
                "phase_name": "深度分析阶段", 
                "description": "深入分析关键问题",
                "duration_days": 10,
                "tasks": ["问题分解", "案例分析", "对比研究"],
                "deliverables": ["分析报告", "关键发现"]
            },
            {
                "phase_name": "综合总结阶段",
                "description": "综合所有发现并形成结论",
                "duration_days": 5,
                "tasks": ["发现整合", "结论形成", "报告撰写"],
                "deliverables": ["最终报告", "研究洞察"]
            }
        ]
        return phases
    
    def _create_timeline(self, state: ResearchPlanningState) -> Dict[str, Any]:
        """创建时间线"""
        return {
            "total_duration_days": 22,
            "start_date": datetime.utcnow().isoformat(),
            "milestones": [
                {"name": "文献调研完成", "day": 7},
                {"name": "深度分析完成", "day": 17},
                {"name": "研究完成", "day": 22}
            ]
        }
    
    def _identify_resources(self, state: ResearchPlanningState) -> List[str]:
        """识别所需资源"""
        return [
            "学术数据库访问权限",
            "专业分析工具",
            "领域专家咨询",
            "计算资源"
        ]
    
    def _define_success_criteria(self, state: ResearchPlanningState) -> List[str]:
        """定义成功标准"""
        return [
            "回答所有核心研究问题",
            "发现至少3个关键洞察",
            "形成可执行的建议",
            "建立完整的知识体系"
        ]
    
    def _assess_risks(self, state: ResearchPlanningState) -> List[Dict[str, Any]]:
        """评估风险"""
        return [
            {
                "risk": "信息源不足",
                "probability": "中",
                "impact": "高",
                "mitigation": "扩大搜索范围，寻找替代信息源"
            },
            {
                "risk": "时间超期",
                "probability": "中",
                "impact": "中",
                "mitigation": "优先处理核心问题，必要时调整范围"
            }
        ]
    
    async def _execute_search_strategy(self, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行搜索策略"""
        # 这里应该集成实际的搜索API
        # 目前返回模拟数据
        return [
            {
                "title": f"关于{strategy.get('target_question', '未知主题')}的研究",
                "source": "模拟数据源",
                "summary": "这是一个模拟的搜索结果",
                "relevance_score": 0.8,
                "publication_date": "2024-01-01"
            }
        ]
    
    async def plan_research(
        self,
        project_id: str,
        research_topic: str,
        research_objectives: List[str],
        domain_context: Optional[str] = None,
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """研究规划的主入口"""
        
        # 初始化状态
        initial_state = ResearchPlanningState(
            project_id=project_id,
            research_topic=research_topic,
            research_objectives=research_objectives,
            domain_context=domain_context,
            existing_knowledge=None,
            research_questions=None,
            search_strategies=None,
            information_gaps=None,
            research_plan=None,
            execution_timeline=None,
            current_phase="planning",
            completed_tasks=[],
            collected_information=[],
            synthesized_insights=None,
            planning_status="pending",
            current_step="init",
            error_message=None,
            warnings=[],
            result=None
        )
        
        try:
            # 执行工作流
            final_state = await self.graph.ainvoke(initial_state)
            return final_state.get("result", {})
            
        except Exception as e:
            logger.error(f"研究规划工作流执行失败: {e}")
            
            error_result = {
                "project_id": project_id,
                "research_topic": research_topic,
                "planning_status": "failed",
                "error_message": str(e)
            }
            
            return error_result


# 全局研究规划智能体实例
_research_planning_agent = None

def get_research_planning_agent() -> ResearchPlanningAgent:
    """获取研究规划智能体实例（单例模式）"""
    global _research_planning_agent
    if _research_planning_agent is None:
        _research_planning_agent = ResearchPlanningAgent()
    return _research_planning_agent 