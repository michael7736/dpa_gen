"""
Multi-dimensional Outline Agent - 多维大纲提取Agent
从逻辑、主题、时间、因果等多个维度解析文档结构
"""

import json
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from langchain_core.messages import HumanMessage, SystemMessage
from .base import BaseAgent
from ..prompts.templates import get_prompt_template
from ...utils.logger import get_logger

logger = get_logger(__name__)


class OutlineDimension(Enum):
    """大纲维度枚举"""
    LOGICAL = "logical"         # 逻辑大纲：章节结构和论述流程
    THEMATIC = "thematic"       # 主题大纲：概念网络和重要性
    TEMPORAL = "temporal"       # 时间线大纲：时序信息和事件
    CAUSAL = "causal"          # 因果链大纲：原因-结果关系
    ALL = "all"                # 所有维度


class OutlineAgent(BaseAgent):
    """多维大纲提取Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(name="OutlineAgent", temperature=0.2, **kwargs)
        self.outline_cache = {}  # 缓存大纲结果
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        提取多维度大纲
        
        Args:
            input_data: 包含document_content、dimension等
            context: 上下文信息
            
        Returns:
            多维大纲结果
        """
        start_time = time.time()
        
        try:
            # 验证输入
            if not await self.validate_input(input_data):
                raise ValueError("Invalid input data")
            
            document_content = input_data["document_content"]
            dimension = input_data.get("dimension", OutlineDimension.ALL.value)
            document_id = input_data.get("document_id")
            
            # 获取缓存键
            cache_key = f"{document_id}_{dimension}"
            
            # 检查缓存
            if cache_key in self.outline_cache:
                logger.info(f"Using cached outline for {cache_key}")
                return {
                    "success": True,
                    "result": self.outline_cache[cache_key],
                    "metadata": {
                        "agent": self.name,
                        "duration": 0,
                        "tokens_used": 0,
                        "from_cache": True,
                        "dimension": dimension
                    }
                }
            
            # 生成大纲
            if dimension == OutlineDimension.ALL.value:
                outline_result = await self._generate_all_outlines(document_content)
            else:
                outline_result = await self._generate_single_outline(
                    document_content, dimension
                )
            
            # 缓存结果
            if document_id:
                self.outline_cache[cache_key] = outline_result
            
            # 计算token使用量
            tokens_used = self._estimate_tokens(document_content, outline_result)
            
            # 记录性能指标
            end_time = time.time()
            self.log_metrics(start_time, end_time, tokens_used, True)
            
            # 更新上下文
            if context:
                context = self.update_context(context, {
                    f"outline_{dimension}": outline_result,
                    "outline_extracted": True
                })
            
            return {
                "success": True,
                "result": outline_result,
                "metadata": {
                    "agent": self.name,
                    "duration": end_time - start_time,
                    "tokens_used": tokens_used,
                    "dimension": dimension,
                    "from_cache": False
                }
            }
            
        except Exception as e:
            logger.error(f"Error in OutlineAgent: {str(e)}", exc_info=True)
            end_time = time.time()
            self.log_metrics(start_time, end_time, 0, False)
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "agent": self.name,
                    "duration": end_time - start_time
                }
            }
    
    async def _generate_single_outline(
        self, document_content: str, dimension: str
    ) -> Dict[str, Any]:
        """生成单个维度的大纲"""
        # 限制内容长度
        max_length = 16000
        if len(document_content) > max_length:
            document_content = document_content[:max_length] + "\n\n[内容已截断...]"
        
        # 使用通用的多维大纲模板
        prompt_template = get_prompt_template("outline")
        prompt = prompt_template.format(document_content=document_content)
        
        # 根据维度添加特定指令
        dimension_instruction = self._get_dimension_instruction(dimension)
        
        messages = [
            SystemMessage(content="你是一位专业的文档结构分析专家，擅长从多个维度解析文档大纲。"),
            HumanMessage(content=prompt + f"\n\n请重点提取{dimension_instruction}")
        ]
        
        response = await self.llm.agenerate([messages])
        result_text = response.generations[0][0].text.strip()
        
        # 解析结果
        outline_data = self._parse_outline_result(result_text)
        
        # 根据维度提取特定大纲
        if dimension == OutlineDimension.LOGICAL.value:
            return self._extract_logical_outline(outline_data)
        elif dimension == OutlineDimension.THEMATIC.value:
            return self._extract_thematic_outline(outline_data)
        elif dimension == OutlineDimension.TEMPORAL.value:
            return self._extract_temporal_outline(outline_data)
        elif dimension == OutlineDimension.CAUSAL.value:
            return self._extract_causal_outline(outline_data)
        else:
            return outline_data
    
    async def _generate_all_outlines(self, document_content: str) -> Dict[str, Any]:
        """生成所有维度的大纲"""
        # 限制内容长度
        max_length = 16000
        if len(document_content) > max_length:
            document_content = document_content[:max_length] + "\n\n[内容已截断...]"
        
        # 使用通用的多维大纲模板
        prompt_template = get_prompt_template("outline")
        prompt = prompt_template.format(document_content=document_content)
        
        messages = [
            SystemMessage(content="你是一位专业的文档结构分析专家，擅长从多个维度解析文档大纲。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.agenerate([messages])
        result_text = response.generations[0][0].text.strip()
        
        # 解析完整结果
        return self._parse_outline_result(result_text)
    
    def _get_dimension_instruction(self, dimension: str) -> str:
        """获取维度特定的指令"""
        instructions = {
            OutlineDimension.LOGICAL.value: "逻辑大纲，包括章节层级结构、各部分的逻辑关系和论述流程",
            OutlineDimension.THEMATIC.value: "主题大纲，识别核心概念、主题网络和概念重要性等级",
            OutlineDimension.TEMPORAL.value: "时间线大纲，提取时序信息、关键时间节点和事件发展脉络",
            OutlineDimension.CAUSAL.value: "因果链大纲，识别原因-结果关系、构建因果推理链条"
        }
        return instructions.get(dimension, "完整的多维度大纲")
    
    def _parse_outline_result(self, result_text: str) -> Dict[str, Any]:
        """解析LLM返回的大纲结果"""
        try:
            # 尝试直接解析JSON
            return json.loads(result_text)
        except json.JSONDecodeError:
            # 如果不是有效的JSON，尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # 如果还是失败，返回结构化的文本结果
            logger.warning("Failed to parse outline result as JSON, returning text structure")
            return self._structure_text_outline(result_text)
    
    def _structure_text_outline(self, text: str) -> Dict[str, Any]:
        """将文本结果结构化"""
        lines = text.strip().split('\n')
        
        # 初始化各维度的容器
        logical_outline = []
        thematic_outline = []
        temporal_outline = []
        causal_outline = []
        
        current_section = None
        current_items = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测维度标题
            if "逻辑大纲" in line or "Logical Outline" in line:
                if current_section and current_items:
                    self._append_to_section(current_section, current_items, 
                                          logical_outline, thematic_outline,
                                          temporal_outline, causal_outline)
                current_section = "logical"
                current_items = []
            elif "主题大纲" in line or "Thematic Outline" in line:
                if current_section and current_items:
                    self._append_to_section(current_section, current_items,
                                          logical_outline, thematic_outline,
                                          temporal_outline, causal_outline)
                current_section = "thematic"
                current_items = []
            elif "时间线大纲" in line or "Temporal Outline" in line:
                if current_section and current_items:
                    self._append_to_section(current_section, current_items,
                                          logical_outline, thematic_outline,
                                          temporal_outline, causal_outline)
                current_section = "temporal"
                current_items = []
            elif "因果链大纲" in line or "Causal Chain Outline" in line:
                if current_section and current_items:
                    self._append_to_section(current_section, current_items,
                                          logical_outline, thematic_outline,
                                          temporal_outline, causal_outline)
                current_section = "causal"
                current_items = []
            elif line.startswith(('-', '•', '*', '·')) or line[0].isdigit():
                # 提取列表项
                content = line.lstrip('-•*·0123456789. ')
                if content:
                    current_items.append(content)
        
        # 处理最后一个部分
        if current_section and current_items:
            self._append_to_section(current_section, current_items,
                                  logical_outline, thematic_outline,
                                  temporal_outline, causal_outline)
        
        return {
            "logical_outline": logical_outline,
            "thematic_outline": thematic_outline,
            "temporal_outline": temporal_outline,
            "causal_chain_outline": causal_outline
        }
    
    def _append_to_section(self, section: str, items: List[str],
                          logical: List, thematic: List,
                          temporal: List, causal: List):
        """将项目添加到对应的维度"""
        if section == "logical":
            logical.extend(items)
        elif section == "thematic":
            thematic.extend(items)
        elif section == "temporal":
            temporal.extend(items)
        elif section == "causal":
            causal.extend(items)
    
    def _extract_logical_outline(self, outline_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取逻辑大纲"""
        if "logical_outline" in outline_data:
            return {
                "dimension": "logical",
                "outline": outline_data["logical_outline"],
                "summary": "文档的逻辑结构和章节层级"
            }
        
        # 构建默认结构
        return {
            "dimension": "logical",
            "outline": self._build_logical_structure(outline_data),
            "summary": "文档的逻辑结构分析"
        }
    
    def _extract_thematic_outline(self, outline_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取主题大纲"""
        if "thematic_outline" in outline_data:
            return {
                "dimension": "thematic",
                "outline": outline_data["thematic_outline"],
                "summary": "文档的主题网络和概念关系"
            }
        
        return {
            "dimension": "thematic",
            "outline": self._build_thematic_structure(outline_data),
            "summary": "文档的主题分析"
        }
    
    def _extract_temporal_outline(self, outline_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取时间线大纲"""
        if "temporal_outline" in outline_data:
            return {
                "dimension": "temporal",
                "outline": outline_data["temporal_outline"],
                "summary": "文档的时间线和事件序列"
            }
        
        return {
            "dimension": "temporal",
            "outline": self._build_temporal_structure(outline_data),
            "summary": "文档的时序分析"
        }
    
    def _extract_causal_outline(self, outline_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取因果链大纲"""
        if "causal_chain_outline" in outline_data:
            return {
                "dimension": "causal",
                "outline": outline_data["causal_chain_outline"],
                "summary": "文档的因果关系链"
            }
        
        return {
            "dimension": "causal",
            "outline": self._build_causal_structure(outline_data),
            "summary": "文档的因果分析"
        }
    
    def _build_logical_structure(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建逻辑结构"""
        # 简单实现，实际应该基于数据构建
        return [
            {"level": 1, "title": "引言", "type": "introduction"},
            {"level": 1, "title": "主体", "type": "main_body"},
            {"level": 1, "title": "结论", "type": "conclusion"}
        ]
    
    def _build_thematic_structure(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建主题结构"""
        return [
            {"theme": "核心概念", "importance": "high", "frequency": 10},
            {"theme": "相关概念", "importance": "medium", "frequency": 5}
        ]
    
    def _build_temporal_structure(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建时间结构"""
        return [
            {"time": "开始", "event": "项目启动", "importance": "high"},
            {"time": "进行中", "event": "开发阶段", "importance": "medium"},
            {"time": "结束", "event": "项目完成", "importance": "high"}
        ]
    
    def _build_causal_structure(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建因果结构"""
        return [
            {"cause": "原因A", "effect": "结果B", "strength": 0.8},
            {"cause": "原因C", "effect": "结果D", "strength": 0.6}
        ]
    
    def _estimate_tokens(self, content: str, result: Dict[str, Any]) -> int:
        """估算token使用量"""
        # 简单估算：每4个字符约1个token
        input_tokens = len(content) // 4
        output_tokens = len(str(result)) // 4
        return input_tokens + output_tokens
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ["document_content"]
        
        for field in required_fields:
            if field not in input_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        if not input_data["document_content"] or len(input_data["document_content"]) < 10:
            logger.error("Document content is empty or too short")
            return False
        
        # 验证维度
        if "dimension" in input_data:
            valid_dimensions = [dim.value for dim in OutlineDimension]
            if input_data["dimension"] not in valid_dimensions:
                logger.error(f"Invalid dimension: {input_data['dimension']}")
                return False
        
        return True
    
    async def analyze_document_structure(
        self, document_content: str, document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析文档结构的便捷方法
        
        Args:
            document_content: 文档内容
            document_id: 文档ID（用于缓存）
            
        Returns:
            完整的文档结构分析
        """
        # 生成所有维度的大纲
        all_outlines = await self.process({
            "document_content": document_content,
            "document_id": document_id,
            "dimension": OutlineDimension.ALL.value
        })
        
        if not all_outlines["success"]:
            return all_outlines
        
        # 分析大纲间的关系
        outline_data = all_outlines["result"]
        
        # 构建综合分析
        analysis = {
            "outlines": outline_data,
            "structure_summary": self._generate_structure_summary(outline_data),
            "key_insights": self._extract_key_insights(outline_data),
            "recommendations": self._generate_recommendations(outline_data)
        }
        
        return {
            "success": True,
            "result": analysis,
            "metadata": all_outlines["metadata"]
        }
    
    def _generate_structure_summary(self, outline_data: Dict[str, Any]) -> str:
        """生成结构摘要"""
        summary_parts = []
        
        if "logical_outline" in outline_data:
            summary_parts.append("文档具有清晰的逻辑结构")
        
        if "thematic_outline" in outline_data:
            theme_count = len(outline_data.get("thematic_outline", []))
            summary_parts.append(f"包含{theme_count}个主要主题")
        
        if "temporal_outline" in outline_data:
            summary_parts.append("存在时间序列信息")
        
        if "causal_chain_outline" in outline_data:
            summary_parts.append("包含因果关系分析")
        
        return "；".join(summary_parts) if summary_parts else "文档结构分析完成"
    
    def _extract_key_insights(self, outline_data: Dict[str, Any]) -> List[str]:
        """提取关键洞察"""
        insights = []
        
        # 基于大纲数据提取洞察
        if "logical_outline" in outline_data and outline_data["logical_outline"]:
            insights.append("文档遵循标准的学术/技术写作结构")
        
        if "thematic_outline" in outline_data and len(outline_data.get("thematic_outline", [])) > 5:
            insights.append("文档涵盖多个复杂主题，建议分主题深入分析")
        
        if "temporal_outline" in outline_data and outline_data["temporal_outline"]:
            insights.append("文档包含时间敏感信息，需要关注时效性")
        
        if "causal_chain_outline" in outline_data and outline_data["causal_chain_outline"]:
            insights.append("文档存在明确的因果推理，适合用于决策支持")
        
        return insights if insights else ["文档结构完整，适合进行深度分析"]
    
    def _generate_recommendations(self, outline_data: Dict[str, Any]) -> List[str]:
        """生成分析建议"""
        recommendations = []
        
        # 基于大纲特征生成建议
        if "logical_outline" in outline_data:
            recommendations.append("按照逻辑结构进行分段深入分析")
        
        if "thematic_outline" in outline_data and len(outline_data.get("thematic_outline", [])) > 3:
            recommendations.append("创建主题索引和概念图谱")
        
        if "temporal_outline" in outline_data:
            recommendations.append("构建时间轴可视化")
        
        if "causal_chain_outline" in outline_data:
            recommendations.append("生成因果关系图和决策树")
        
        # 添加通用建议
        recommendations.append("使用渐进式摘要功能获取不同粒度的理解")
        
        return recommendations