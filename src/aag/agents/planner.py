"""
分析规划Agent
基于文档特征和用户目标制定最优分析计划
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ..prompts.templates import get_prompt_template
from ..storage import MetadataManager
from ...utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisGoal(Enum):
    """分析目标枚举"""
    QUICK_OVERVIEW = "quick_overview"        # 快速概览
    DEEP_UNDERSTANDING = "deep_understanding"  # 深度理解
    CRITICAL_REVIEW = "critical_review"      # 批判性审查
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"  # 知识提取
    RESEARCH_PLANNING = "research_planning"  # 研究规划
    CUSTOM = "custom"                        # 自定义目标


class DocumentCategory(Enum):
    """文档类别枚举"""
    ACADEMIC_PAPER = "academic_paper"        # 学术论文
    TECHNICAL_REPORT = "technical_report"    # 技术报告
    BUSINESS_DOCUMENT = "business_document"  # 商业文档
    NEWS_ARTICLE = "news_article"           # 新闻文章
    BOOK_CHAPTER = "book_chapter"           # 书籍章节
    GENERAL_TEXT = "general_text"           # 一般文本


class PlannerAgent(BaseAgent):
    """分析规划Agent"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.3):
        super().__init__(name="PlannerAgent", model_name=model_name, temperature=temperature)
        self.metadata_manager = MetadataManager()
        logger.info(f"初始化分析规划Agent，模型: {model_name}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        制定分析计划
        
        Args:
            input_data: 包含以下字段
                - document_content: 文档内容（前8000字符用于评估）
                - document_id: 文档ID
                - analysis_goal: 分析目标（可选）
                - user_requirements: 用户特定需求（可选）
                - time_budget: 时间预算（秒）（可选）
                - cost_budget: 成本预算（美元）（可选）
        
        Returns:
            包含分析计划的字典
        """
        try:
            document_content = input_data["document_content"]
            document_id = input_data["document_id"]
            analysis_goal = input_data.get("analysis_goal", AnalysisGoal.DEEP_UNDERSTANDING.value)
            user_requirements = input_data.get("user_requirements", "")
            time_budget = input_data.get("time_budget", 300)  # 默认5分钟
            cost_budget = input_data.get("cost_budget", 1.0)  # 默认1美元
            
            # 限制文档长度用于评估
            if len(document_content) > 8000:
                document_content = document_content[:8000] + "\n\n[文档内容已截断用于规划...]"
            
            # 检查缓存
            cache_key = self._generate_cache_key(document_id, f"plan_{analysis_goal}")
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"从缓存获取分析计划: {document_id}")
                return {
                    "success": True,
                    "result": cached_result,
                    "metadata": {
                        "duration": 0.0,
                        "tokens_used": 0,
                        "from_cache": True
                    }
                }
            
            # 获取已有的元数据（如果有）
            existing_metadata = await self.metadata_manager.get_metadata(document_id)
            
            # 准备提示词
            prompt_template = get_prompt_template("planner")
            
            # 构建消息
            messages = [
                SystemMessage(content=prompt_template),
                HumanMessage(content=f"""
请为以下文档制定分析计划：

文档内容：
{document_content}

分析目标：{analysis_goal}
{f"用户特定需求：{user_requirements}" if user_requirements else ""}
时间预算：{time_budget}秒
成本预算：${cost_budget}

{f"已有分析信息：{json.dumps(existing_metadata, ensure_ascii=False)}" if existing_metadata else ""}

请按照以下JSON格式返回分析计划：
{{
    "document_assessment": {{
        "category": "文档类别（academic_paper/technical_report/business_document/news_article/book_chapter/general_text）",
        "complexity": "复杂度（low/medium/high）",
        "length": "长度（short/medium/long）",
        "quality": "质量评估（low/medium/high）",
        "key_characteristics": ["特征1", "特征2", "特征3"]
    }},
    "recommended_analyses": [
        {{
            "analysis_type": "分析类型",
            "priority": "优先级（high/medium/low）",
            "estimated_time": 时间（秒）,
            "estimated_cost": 成本（美元）,
            "expected_value": "预期价值描述",
            "dependencies": ["依赖的其他分析"]
        }}
    ],
    "execution_plan": {{
        "phases": [
            {{
                "phase_name": "阶段名称",
                "analyses": ["分析1", "分析2"],
                "parallel": true/false,
                "estimated_time": 时间（秒）,
                "outputs": ["输出1", "输出2"]
            }}
        ],
        "total_time": 总时间（秒）,
        "total_cost": 总成本（美元）,
        "optimization_notes": "优化建议"
    }},
    "alternative_plans": [
        {{
            "name": "替代方案名称",
            "description": "方案描述",
            "time": 时间（秒）,
            "cost": 成本（美元）,
            "trade_offs": "权衡说明"
        }}
    ],
    "warnings": ["警告1", "警告2"],
    "recommendations": ["建议1", "建议2"]
}}
""")
            ]
            
            # 调用LLM
            start_time = self._get_timestamp()
            response = await self.llm.ainvoke(messages)
            duration = self._get_timestamp() - start_time
            
            # 解析响应
            try:
                result = json.loads(response.content)
                
                # 验证和调整计划以符合预算
                result = self._adjust_plan_to_budget(result, time_budget, cost_budget)
                
            except json.JSONDecodeError:
                logger.error(f"分析计划响应解析失败: {response.content}")
                # 返回默认计划
                result = self._create_default_plan(analysis_goal, time_budget, cost_budget)
            
            # 估算token使用量
            tokens_used = self._estimate_tokens(str(messages) + response.content)
            
            # 缓存结果
            await self._cache_result(cache_key, result)
            
            # 更新元数据
            await self.metadata_manager.update_metadata(
                document_id=document_id,
                updates={
                    "has_analysis_plan": True,
                    "analysis_goal": analysis_goal,
                    "planned_analyses": [a["analysis_type"] for a in result.get("recommended_analyses", [])]
                }
            )
            
            return {
                "success": True,
                "result": result,
                "metadata": {
                    "duration": duration,
                    "tokens_used": tokens_used,
                    "from_cache": False
                }
            }
            
        except Exception as e:
            logger.error(f"分析规划失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "duration": 0.0,
                    "tokens_used": 0
                }
            }
    
    def _adjust_plan_to_budget(
        self, 
        plan: Dict[str, Any], 
        time_budget: float, 
        cost_budget: float
    ) -> Dict[str, Any]:
        """调整计划以符合预算限制"""
        execution_plan = plan.get("execution_plan", {})
        total_time = execution_plan.get("total_time", 0)
        total_cost = execution_plan.get("total_cost", 0)
        
        if total_time <= time_budget and total_cost <= cost_budget:
            return plan
        
        # 需要调整计划
        logger.info(f"调整计划以符合预算: 时间 {total_time}s -> {time_budget}s, 成本 ${total_cost} -> ${cost_budget}")
        
        # 按优先级筛选分析
        recommended_analyses = plan.get("recommended_analyses", [])
        high_priority = [a for a in recommended_analyses if a["priority"] == "high"]
        medium_priority = [a for a in recommended_analyses if a["priority"] == "medium"]
        
        # 重新构建计划，优先保留高优先级分析
        adjusted_analyses = []
        current_time = 0
        current_cost = 0
        
        for analysis in high_priority + medium_priority:
            if (current_time + analysis["estimated_time"] <= time_budget and
                current_cost + analysis["estimated_cost"] <= cost_budget):
                adjusted_analyses.append(analysis)
                current_time += analysis["estimated_time"]
                current_cost += analysis["estimated_cost"]
        
        plan["recommended_analyses"] = adjusted_analyses
        plan["execution_plan"]["total_time"] = current_time
        plan["execution_plan"]["total_cost"] = current_cost
        plan["warnings"] = plan.get("warnings", []) + [
            f"计划已调整以符合预算限制（时间: {time_budget}s, 成本: ${cost_budget}）"
        ]
        
        return plan
    
    def _create_default_plan(
        self, 
        analysis_goal: str, 
        time_budget: float, 
        cost_budget: float
    ) -> Dict[str, Any]:
        """创建默认分析计划"""
        default_analyses = {
            AnalysisGoal.QUICK_OVERVIEW.value: [
                ("skim", 5, 0.01, "high"),
                ("summary_level_2", 10, 0.02, "high"),
                ("outline_logical", 15, 0.03, "medium")
            ],
            AnalysisGoal.DEEP_UNDERSTANDING.value: [
                ("skim", 5, 0.01, "high"),
                ("summary_all", 60, 0.15, "high"),
                ("knowledge_graph_comprehensive", 30, 0.10, "high"),
                ("outline_all", 40, 0.08, "medium"),
                ("deep_analysis_all", 60, 0.20, "medium")
            ],
            AnalysisGoal.CRITICAL_REVIEW.value: [
                ("skim", 5, 0.01, "high"),
                ("evidence_chain", 20, 0.05, "high"),
                ("critical_thinking", 25, 0.06, "high"),
                ("cross_reference", 20, 0.05, "medium")
            ],
            AnalysisGoal.KNOWLEDGE_EXTRACTION.value: [
                ("skim", 5, 0.01, "high"),
                ("knowledge_graph_comprehensive", 30, 0.10, "high"),
                ("outline_thematic", 20, 0.04, "high"),
                ("summary_level_3", 15, 0.03, "medium")
            ]
        }
        
        analyses = default_analyses.get(
            analysis_goal, 
            default_analyses[AnalysisGoal.DEEP_UNDERSTANDING.value]
        )
        
        recommended = []
        total_time = 0
        total_cost = 0
        
        for analysis_type, time, cost, priority in analyses:
            if total_time + time <= time_budget and total_cost + cost <= cost_budget:
                recommended.append({
                    "analysis_type": analysis_type,
                    "priority": priority,
                    "estimated_time": time,
                    "estimated_cost": cost,
                    "expected_value": f"{analysis_type}分析结果",
                    "dependencies": []
                })
                total_time += time
                total_cost += cost
        
        return {
            "document_assessment": {
                "category": "general_text",
                "complexity": "medium",
                "length": "medium",
                "quality": "medium",
                "key_characteristics": ["需要进一步评估"]
            },
            "recommended_analyses": recommended,
            "execution_plan": {
                "phases": [{
                    "phase_name": "默认分析",
                    "analyses": [a["analysis_type"] for a in recommended],
                    "parallel": False,
                    "estimated_time": total_time,
                    "outputs": ["分析结果"]
                }],
                "total_time": total_time,
                "total_cost": total_cost,
                "optimization_notes": "这是基于目标的默认计划"
            },
            "alternative_plans": [],
            "warnings": ["使用默认计划，可能不是最优"],
            "recommendations": ["建议人工审查和调整计划"]
        }
    
    async def evaluate_progress(
        self, 
        document_id: str, 
        plan: Dict[str, Any],
        completed_analyses: List[str]
    ) -> Dict[str, Any]:
        """
        评估分析进度并提供调整建议
        
        Args:
            document_id: 文档ID
            plan: 原始分析计划
            completed_analyses: 已完成的分析列表
        
        Returns:
            进度评估和调整建议
        """
        try:
            recommended_analyses = plan.get("recommended_analyses", [])
            total_analyses = len(recommended_analyses)
            completed_count = len(completed_analyses)
            
            # 计算完成度
            completion_rate = completed_count / total_analyses if total_analyses > 0 else 0
            
            # 识别未完成的分析
            pending_analyses = [
                a for a in recommended_analyses 
                if a["analysis_type"] not in completed_analyses
            ]
            
            # 计算剩余时间和成本
            remaining_time = sum(a["estimated_time"] for a in pending_analyses)
            remaining_cost = sum(a["estimated_cost"] for a in pending_analyses)
            
            # 生成进度报告
            progress_report = {
                "completion_rate": completion_rate,
                "completed_analyses": completed_analyses,
                "pending_analyses": [a["analysis_type"] for a in pending_analyses],
                "remaining_time": remaining_time,
                "remaining_cost": remaining_cost,
                "status": self._get_progress_status(completion_rate),
                "recommendations": self._get_progress_recommendations(
                    completion_rate, 
                    pending_analyses
                )
            }
            
            return {
                "success": True,
                "result": progress_report,
                "metadata": {
                    "document_id": document_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"进度评估失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_progress_status(self, completion_rate: float) -> str:
        """根据完成率返回状态"""
        if completion_rate == 0:
            return "未开始"
        elif completion_rate < 0.25:
            return "刚开始"
        elif completion_rate < 0.5:
            return "进行中"
        elif completion_rate < 0.75:
            return "过半"
        elif completion_rate < 1.0:
            return "即将完成"
        else:
            return "已完成"
    
    def _get_progress_recommendations(
        self, 
        completion_rate: float, 
        pending_analyses: List[Dict[str, Any]]
    ) -> List[str]:
        """生成进度建议"""
        recommendations = []
        
        if completion_rate == 1.0:
            recommendations.append("所有计划的分析已完成")
        else:
            # 找出高优先级未完成的分析
            high_priority_pending = [
                a for a in pending_analyses 
                if a["priority"] == "high"
            ]
            
            if high_priority_pending:
                recommendations.append(
                    f"建议优先完成{len(high_priority_pending)}个高优先级分析"
                )
            
            if completion_rate < 0.5 and len(pending_analyses) > 5:
                recommendations.append("考虑简化分析计划以加快进度")
            
            if completion_rate > 0.7:
                recommendations.append("即将完成，保持当前进度")
        
        return recommendations