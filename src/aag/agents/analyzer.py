"""
深度分析Agent集合
提供多种专门的分析视角和方法
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ..prompts.templates import get_prompt_template
from ..storage import ArtifactStore
from ...utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisType(Enum):
    """分析类型枚举"""
    EVIDENCE_CHAIN = "evidence_chain"        # 证据链跟踪
    CROSS_REFERENCE = "cross_reference"      # 交叉引用分析
    CRITICAL_THINKING = "critical_thinking"  # 批判性思维分析


class EvidenceChainAnalyzer(BaseAgent):
    """证据链跟踪分析Agent"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        super().__init__(name="EvidenceChainAnalyzer", model_name=model_name, temperature=temperature)
        self.analysis_type = AnalysisType.EVIDENCE_CHAIN
        logger.info(f"初始化证据链分析Agent，模型: {model_name}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行证据链跟踪分析
        
        Args:
            input_data: 包含以下字段
                - document_content: 文档内容
                - document_id: 文档ID
                - focus_claims: 可选，聚焦分析的声明列表
        
        Returns:
            包含分析结果的字典
        """
        try:
            document_content = input_data["document_content"]
            document_id = input_data["document_id"]
            focus_claims = input_data.get("focus_claims", [])
            
            # 检查缓存
            cache_key = self._generate_cache_key(document_id, self.analysis_type.value)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"从缓存获取证据链分析结果: {document_id}")
                return {
                    "success": True,
                    "result": cached_result,
                    "metadata": {
                        "duration": 0.0,
                        "tokens_used": 0,
                        "from_cache": True
                    }
                }
            
            # 准备提示词
            prompt_template = get_prompt_template("evidence_chain_analysis")
            
            # 构建消息
            messages = [
                SystemMessage(content=prompt_template),
                HumanMessage(content=f"""
分析以下文档的证据链：

文档内容：
{document_content}

{f"重点关注以下声明：{', '.join(focus_claims)}" if focus_claims else "请识别并分析文档中的所有重要声明。"}

请按照以下格式返回JSON结果：
{{
    "claims": [
        {{
            "claim": "具体的声明内容",
            "importance": "高/中/低",
            "evidence": [
                {{
                    "type": "数据/引用/案例/逻辑推理",
                    "content": "证据内容",
                    "strength": "强/中/弱",
                    "location": "证据在文档中的位置"
                }}
            ],
            "evidence_quality": "证据质量评估",
            "gaps": ["缺失的证据或论证"]
        }}
    ],
    "evidence_chains": [
        {{
            "chain_description": "证据链描述",
            "links": ["证据1", "推理过程", "证据2", "结论"],
            "strength": "链条强度评估",
            "weak_points": ["薄弱环节"]
        }}
    ],
    "overall_assessment": {{
        "evidence_completeness": "整体证据完整性评分(1-10)",
        "logical_coherence": "逻辑连贯性评分(1-10)",
        "credibility": "可信度评分(1-10)",
        "key_insights": ["关键洞察"],
        "recommendations": ["改进建议"]
    }}
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
            except json.JSONDecodeError:
                logger.error(f"证据链分析响应解析失败: {response.content}")
                result = {
                    "claims": [],
                    "evidence_chains": [],
                    "overall_assessment": {
                        "error": "响应解析失败",
                        "raw_response": response.content[:500]
                    }
                }
            
            # 估算token使用量
            tokens_used = self._estimate_tokens(str(messages) + response.content)
            
            # 缓存结果
            await self._cache_result(cache_key, result)
            
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
            logger.error(f"证据链分析失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "duration": 0.0,
                    "tokens_used": 0
                }
            }


class CrossReferenceAnalyzer(BaseAgent):
    """交叉引用分析Agent"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        super().__init__(name="CrossReferenceAnalyzer", model_name=model_name, temperature=temperature)
        self.analysis_type = AnalysisType.CROSS_REFERENCE
        logger.info(f"初始化交叉引用分析Agent，模型: {model_name}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行交叉引用分析
        
        Args:
            input_data: 包含以下字段
                - document_content: 文档内容
                - document_id: 文档ID
                - reference_docs: 可选，参考文档列表
        
        Returns:
            包含分析结果的字典
        """
        try:
            document_content = input_data["document_content"]
            document_id = input_data["document_id"]
            reference_docs = input_data.get("reference_docs", [])
            
            # 检查缓存
            cache_key = self._generate_cache_key(document_id, self.analysis_type.value)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"从缓存获取交叉引用分析结果: {document_id}")
                return {
                    "success": True,
                    "result": cached_result,
                    "metadata": {
                        "duration": 0.0,
                        "tokens_used": 0,
                        "from_cache": True
                    }
                }
            
            # 准备提示词
            prompt_template = get_prompt_template("cross_reference_analysis")
            
            # 构建消息
            messages = [
                SystemMessage(content=prompt_template),
                HumanMessage(content=f"""
分析以下文档的交叉引用和内部一致性：

文档内容：
{document_content}

{f"参考文档：{reference_docs}" if reference_docs else ""}

请按照以下格式返回JSON结果：
{{
    "internal_references": [
        {{
            "from_section": "引用来源章节",
            "to_section": "被引用章节",
            "reference_type": "前向引用/后向引用/循环引用",
            "content": "引用内容",
            "consistency": "一致/不一致/部分一致",
            "notes": "备注"
        }}
    ],
    "concept_references": [
        {{
            "concept": "概念名称",
            "definitions": [
                {{
                    "location": "定义位置",
                    "definition": "定义内容"
                }}
            ],
            "usages": [
                {{
                    "location": "使用位置",
                    "context": "使用上下文",
                    "consistency_with_definition": "是否与定义一致"
                }}
            ],
            "evolution": "概念在文档中的演变"
        }}
    ],
    "external_references": [
        {{
            "source": "外部来源",
            "type": "论文/书籍/网站/其他",
            "relevance": "相关性评估",
            "credibility": "可信度评估",
            "usage_context": "引用上下文"
        }}
    ],
    "consistency_analysis": {{
        "terminology_consistency": "术语一致性评分(1-10)",
        "logical_consistency": "逻辑一致性评分(1-10)",
        "data_consistency": "数据一致性评分(1-10)",
        "inconsistencies": [
            {{
                "type": "术语/逻辑/数据",
                "description": "不一致描述",
                "locations": ["位置1", "位置2"],
                "severity": "严重/中等/轻微"
            }}
        ]
    }},
    "reference_network": {{
        "density": "引用网络密度评估",
        "key_nodes": ["关键节点概念"],
        "isolated_sections": ["孤立章节"],
        "insights": ["网络结构洞察"]
    }}
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
            except json.JSONDecodeError:
                logger.error(f"交叉引用分析响应解析失败: {response.content}")
                result = {
                    "internal_references": [],
                    "concept_references": [],
                    "external_references": [],
                    "consistency_analysis": {
                        "error": "响应解析失败",
                        "raw_response": response.content[:500]
                    },
                    "reference_network": {}
                }
            
            # 估算token使用量
            tokens_used = self._estimate_tokens(str(messages) + response.content)
            
            # 缓存结果
            await self._cache_result(cache_key, result)
            
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
            logger.error(f"交叉引用分析失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "duration": 0.0,
                    "tokens_used": 0
                }
            }


class CriticalThinkingAnalyzer(BaseAgent):
    """批判性思维分析Agent"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.3):
        super().__init__(name="CriticalThinkingAnalyzer", model_name=model_name, temperature=temperature)
        self.analysis_type = AnalysisType.CRITICAL_THINKING
        logger.info(f"初始化批判性思维分析Agent，模型: {model_name}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行批判性思维分析
        
        Args:
            input_data: 包含以下字段
                - document_content: 文档内容
                - document_id: 文档ID
                - analysis_depth: 分析深度（basic/deep/comprehensive）
        
        Returns:
            包含分析结果的字典
        """
        try:
            document_content = input_data["document_content"]
            document_id = input_data["document_id"]
            analysis_depth = input_data.get("analysis_depth", "deep")
            
            # 检查缓存
            cache_key = self._generate_cache_key(
                document_id, 
                f"{self.analysis_type.value}_{analysis_depth}"
            )
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"从缓存获取批判性思维分析结果: {document_id}")
                return {
                    "success": True,
                    "result": cached_result,
                    "metadata": {
                        "duration": 0.0,
                        "tokens_used": 0,
                        "from_cache": True
                    }
                }
            
            # 准备提示词
            prompt_template = get_prompt_template("critical_thinking_analysis")
            
            # 构建消息
            messages = [
                SystemMessage(content=prompt_template),
                HumanMessage(content=f"""
对以下文档进行批判性思维分析（分析深度：{analysis_depth}）：

文档内容：
{document_content}

请按照以下格式返回JSON结果：
{{
    "arguments": [
        {{
            "argument": "论点内容",
            "type": "主要论点/次要论点/隐含论点",
            "premises": ["前提1", "前提2"],
            "conclusion": "结论",
            "logical_structure": "演绎/归纳/类比/因果",
            "strength": "强/中/弱",
            "fallacies": [
                {{
                    "type": "谬误类型",
                    "description": "谬误描述",
                    "impact": "对论证的影响"
                }}
            ]
        }}
    ],
    "assumptions": [
        {{
            "assumption": "假设内容",
            "type": "明确的/隐含的",
            "validity": "合理/可疑/不合理",
            "impact": "对结论的影响",
            "alternatives": ["替代假设"]
        }}
    ],
    "biases": [
        {{
            "bias_type": "确认偏见/选择偏见/锚定偏见/其他",
            "description": "偏见描述",
            "evidence": "表现证据",
            "impact": "对分析的影响"
        }}
    ],
    "evidence_evaluation": [
        {{
            "evidence": "证据内容",
            "source_credibility": "来源可信度(1-10)",
            "relevance": "相关性(1-10)",
            "sufficiency": "充分性(1-10)",
            "potential_issues": ["潜在问题"]
        }}
    ],
    "alternative_perspectives": [
        {{
            "perspective": "观点描述",
            "supporting_evidence": ["支持证据"],
            "comparison_with_original": "与原文观点的比较",
            "validity": "合理性评估"
        }}
    ],
    "critical_assessment": {{
        "logical_rigor": "逻辑严密性评分(1-10)",
        "evidence_quality": "证据质量评分(1-10)",
        "objectivity": "客观性评分(1-10)",
        "completeness": "完整性评分(1-10)",
        "strengths": ["优点"],
        "weaknesses": ["缺点"],
        "questions_raised": ["引发的问题"],
        "recommendations": ["改进建议"]
    }}
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
            except json.JSONDecodeError:
                logger.error(f"批判性思维分析响应解析失败: {response.content}")
                result = {
                    "arguments": [],
                    "assumptions": [],
                    "biases": [],
                    "evidence_evaluation": [],
                    "alternative_perspectives": [],
                    "critical_assessment": {
                        "error": "响应解析失败",
                        "raw_response": response.content[:500]
                    }
                }
            
            # 估算token使用量
            tokens_used = self._estimate_tokens(str(messages) + response.content)
            
            # 缓存结果
            await self._cache_result(cache_key, result)
            
            return {
                "success": True,
                "result": result,
                "metadata": {
                    "duration": duration,
                    "tokens_used": tokens_used,
                    "from_cache": False,
                    "analysis_depth": analysis_depth
                }
            }
            
        except Exception as e:
            logger.error(f"批判性思维分析失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "duration": 0.0,
                    "tokens_used": 0
                }
            }


class DeepAnalyzer:
    """深度分析器 - 协调多个分析Agent"""
    
    def __init__(self):
        self.evidence_analyzer = EvidenceChainAnalyzer()
        self.cross_ref_analyzer = CrossReferenceAnalyzer()
        self.critical_analyzer = CriticalThinkingAnalyzer()
        self.artifact_store = ArtifactStore()
        logger.info("初始化深度分析器")
    
    async def analyze(
        self,
        document_content: str,
        document_id: str,
        analysis_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行深度分析
        
        Args:
            document_content: 文档内容
            document_id: 文档ID
            analysis_types: 要执行的分析类型列表
            **kwargs: 其他参数
        
        Returns:
            包含所有分析结果的字典
        """
        if analysis_types is None:
            analysis_types = [
                AnalysisType.EVIDENCE_CHAIN.value,
                AnalysisType.CROSS_REFERENCE.value,
                AnalysisType.CRITICAL_THINKING.value
            ]
        
        results = {}
        total_duration = 0.0
        total_tokens = 0
        
        # 执行各类分析
        for analysis_type in analysis_types:
            try:
                if analysis_type == AnalysisType.EVIDENCE_CHAIN.value:
                    result = await self.evidence_analyzer.process({
                        "document_content": document_content,
                        "document_id": document_id,
                        "focus_claims": kwargs.get("focus_claims", [])
                    })
                elif analysis_type == AnalysisType.CROSS_REFERENCE.value:
                    result = await self.cross_ref_analyzer.process({
                        "document_content": document_content,
                        "document_id": document_id,
                        "reference_docs": kwargs.get("reference_docs", [])
                    })
                elif analysis_type == AnalysisType.CRITICAL_THINKING.value:
                    result = await self.critical_analyzer.process({
                        "document_content": document_content,
                        "document_id": document_id,
                        "analysis_depth": kwargs.get("analysis_depth", "deep")
                    })
                else:
                    logger.warning(f"未知的分析类型: {analysis_type}")
                    continue
                
                if result["success"]:
                    results[analysis_type] = result["result"]
                    total_duration += result["metadata"]["duration"]
                    total_tokens += result["metadata"]["tokens_used"]
                    
                    # 保存到物料库
                    await self.artifact_store.save_artifact(
                        document_id=document_id,
                        analysis_type=f"deep_analysis_{analysis_type}",
                        content=result["result"],
                        execution_time_seconds=int(result["metadata"]["duration"]),
                        token_usage=result["metadata"]["tokens_used"],
                        model_used="gpt-4o-mini",
                        created_by="system"
                    )
                else:
                    results[analysis_type] = {"error": result.get("error", "分析失败")}
                    
            except Exception as e:
                logger.error(f"{analysis_type}分析失败: {str(e)}", exc_info=True)
                results[analysis_type] = {"error": str(e)}
        
        return {
            "success": True,
            "document_id": document_id,
            "analyses": results,
            "metadata": {
                "total_duration": total_duration,
                "total_tokens": total_tokens,
                "analysis_count": len(results)
            }
        }