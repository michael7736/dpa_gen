"""
Progressive Summary Agent - 渐进式摘要Agent
支持多级摘要生成，从50字到2000字
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


class SummaryLevel(Enum):
    """摘要级别枚举"""
    LEVEL_1 = "level_1"  # 50字极简摘要
    LEVEL_2 = "level_2"  # 200字概要
    LEVEL_3 = "level_3"  # 500字详细摘要
    LEVEL_4 = "level_4"  # 1000字深度摘要
    LEVEL_5 = "level_5"  # 2000字完整报告


class ProgressiveSummaryAgent(BaseAgent):
    """渐进式摘要Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(name="ProgressiveSummaryAgent", temperature=0.3, **kwargs)
        self.summary_cache = {}  # 缓存各级摘要结果
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成渐进式摘要
        
        Args:
            input_data: 包含document_content、summary_level、previous_summaries
            context: 上下文信息
            
        Returns:
            摘要结果
        """
        start_time = time.time()
        
        try:
            # 验证输入
            if not await self.validate_input(input_data):
                raise ValueError("Invalid input data")
            
            document_content = input_data["document_content"]
            summary_level = input_data.get("summary_level", SummaryLevel.LEVEL_2.value)
            previous_summaries = input_data.get("previous_summaries", {})
            
            # 获取文档ID用于缓存
            document_id = input_data.get("document_id")
            
            # 检查缓存
            cache_key = f"{document_id}_{summary_level}"
            if cache_key in self.summary_cache:
                cached_result = self.summary_cache[cache_key]
                logger.info(f"Using cached summary for {cache_key}")
                return {
                    "success": True,
                    "result": cached_result,
                    "metadata": {
                        "agent": self.name,
                        "duration": 0,
                        "tokens_used": 0,
                        "from_cache": True,
                        "summary_level": summary_level
                    }
                }
            
            # 生成摘要
            summary_result = await self._generate_summary(
                document_content,
                summary_level,
                previous_summaries
            )
            
            # 缓存结果
            if document_id:
                self.summary_cache[cache_key] = summary_result
            
            # 计算token使用量
            tokens_used = self._estimate_tokens(document_content, summary_result)
            
            # 记录性能指标
            end_time = time.time()
            self.log_metrics(start_time, end_time, tokens_used, True)
            
            # 更新上下文
            if context:
                context = self.update_context(context, {
                    f"summary_{summary_level}": summary_result,
                    "summary_completed": True
                })
            
            return {
                "success": True,
                "result": summary_result,
                "metadata": {
                    "agent": self.name,
                    "duration": end_time - start_time,
                    "tokens_used": tokens_used,
                    "summary_level": summary_level,
                    "from_cache": False
                }
            }
            
        except Exception as e:
            logger.error(f"Error in ProgressiveSummaryAgent: {str(e)}", exc_info=True)
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
    
    async def _generate_summary(
        self,
        document_content: str,
        summary_level: str,
        previous_summaries: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        生成指定级别的摘要
        
        Args:
            document_content: 文档内容
            summary_level: 摘要级别
            previous_summaries: 之前级别的摘要
            
        Returns:
            摘要结果
        """
        # 根据摘要级别调整内容长度
        max_content_length = self._get_max_content_length(summary_level)
        if len(document_content) > max_content_length:
            document_content = document_content[:max_content_length] + "\n\n[内容已截断...]"
        
        # 获取对应级别的提示词模板
        prompt_template = get_prompt_template(f"progressive_summary_{summary_level}")
        
        # 构建提示词参数
        prompt_vars = {"document_content": document_content}
        
        # 添加之前级别的摘要作为参考
        if summary_level == SummaryLevel.LEVEL_2.value and SummaryLevel.LEVEL_1.value in previous_summaries:
            prompt_vars["level_1_summary"] = previous_summaries[SummaryLevel.LEVEL_1.value]
        elif summary_level == SummaryLevel.LEVEL_3.value:
            if SummaryLevel.LEVEL_1.value in previous_summaries:
                prompt_vars["level_1_summary"] = previous_summaries[SummaryLevel.LEVEL_1.value]
            if SummaryLevel.LEVEL_2.value in previous_summaries:
                prompt_vars["level_2_summary"] = previous_summaries[SummaryLevel.LEVEL_2.value]
        elif summary_level == SummaryLevel.LEVEL_4.value:
            if SummaryLevel.LEVEL_2.value in previous_summaries:
                prompt_vars["level_2_summary"] = previous_summaries[SummaryLevel.LEVEL_2.value]
        elif summary_level == SummaryLevel.LEVEL_5.value:
            if SummaryLevel.LEVEL_4.value in previous_summaries:
                prompt_vars["level_4_summary"] = previous_summaries[SummaryLevel.LEVEL_4.value]
        
        prompt = prompt_template.format(**prompt_vars)
        
        # 调用LLM
        messages = [
            SystemMessage(content="你是一位专业的文档摘要专家，擅长提取关键信息并生成不同详细程度的摘要。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.agenerate([messages])
        summary_text = response.generations[0][0].text.strip()
        
        # 根据级别构建结果
        result = {
            "summary": summary_text,
            "level": summary_level,
            "word_count": len(summary_text),
            "key_points": self._extract_key_points(summary_text, summary_level)
        }
        
        # 对于高级别摘要，添加结构化信息
        if summary_level in [SummaryLevel.LEVEL_4.value, SummaryLevel.LEVEL_5.value]:
            result["sections"] = self._extract_sections(summary_text)
            result["recommendations"] = self._extract_recommendations(summary_text)
        
        return result
    
    def _get_max_content_length(self, summary_level: str) -> int:
        """根据摘要级别获取最大内容长度"""
        length_map = {
            SummaryLevel.LEVEL_1.value: 4000,   # ~1000 tokens
            SummaryLevel.LEVEL_2.value: 8000,   # ~2000 tokens
            SummaryLevel.LEVEL_3.value: 16000,  # ~4000 tokens
            SummaryLevel.LEVEL_4.value: 32000,  # ~8000 tokens
            SummaryLevel.LEVEL_5.value: 64000,  # ~16000 tokens
        }
        return length_map.get(summary_level, 8000)
    
    def _extract_key_points(self, summary: str, level: str) -> List[str]:
        """从摘要中提取关键点"""
        # 简单实现：按句号分割，取前N个句子
        sentences = [s.strip() for s in summary.split('。') if s.strip()]
        
        key_points_count = {
            SummaryLevel.LEVEL_1.value: 1,
            SummaryLevel.LEVEL_2.value: 3,
            SummaryLevel.LEVEL_3.value: 5,
            SummaryLevel.LEVEL_4.value: 7,
            SummaryLevel.LEVEL_5.value: 10,
        }
        
        count = key_points_count.get(level, 3)
        return sentences[:count]
    
    def _extract_sections(self, summary: str) -> List[Dict[str, str]]:
        """提取摘要的章节结构"""
        sections = []
        current_section = None
        
        for line in summary.split('\n'):
            line = line.strip()
            if line.startswith('##'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "title": line.replace('##', '').strip(),
                    "content": ""
                }
            elif current_section and line:
                current_section["content"] += line + " "
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _extract_recommendations(self, summary: str) -> List[str]:
        """提取建议和推荐"""
        recommendations = []
        
        # 查找包含建议相关关键词的句子
        keywords = ['建议', '推荐', '应该', '需要', '可以考虑', '最好']
        sentences = summary.split('。')
        
        for sentence in sentences:
            if any(keyword in sentence for keyword in keywords):
                recommendations.append(sentence.strip())
        
        return recommendations[:5]  # 最多返回5条建议
    
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
        
        # 验证摘要级别
        if "summary_level" in input_data:
            valid_levels = [level.value for level in SummaryLevel]
            if input_data["summary_level"] not in valid_levels:
                logger.error(f"Invalid summary level: {input_data['summary_level']}")
                return False
        
        return True
    
    async def generate_all_levels(
        self,
        document_content: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成所有级别的摘要
        
        Args:
            document_content: 文档内容
            document_id: 文档ID（用于缓存）
            
        Returns:
            所有级别的摘要结果
        """
        all_summaries = {}
        previous_summaries = {}
        
        for level in SummaryLevel:
            result = await self.process({
                "document_content": document_content,
                "document_id": document_id,
                "summary_level": level.value,
                "previous_summaries": previous_summaries
            })
            
            if result["success"]:
                all_summaries[level.value] = result["result"]
                # 确保将生成的摘要文本保存到 previous_summaries
                if "summary" in result["result"]:
                    previous_summaries[level.value] = result["result"]["summary"]
                else:
                    # 如果结构不同，尝试提取文本内容
                    previous_summaries[level.value] = str(result["result"])
            else:
                logger.error(f"Failed to generate {level.value} summary: {result.get('error')}")
                break
        
        return all_summaries