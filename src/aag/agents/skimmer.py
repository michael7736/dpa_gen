"""
Skimmer Agent - 快速略读Agent
负责对文档进行快速浏览和初步分析
"""

import json
import time
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .base import BaseAgent
from ..prompts.templates import get_prompt_template
from ...utils.logger import get_logger

logger = get_logger(__name__)


class SkimmerAgent(BaseAgent):
    """快速略读Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(name="SkimmerAgent", temperature=0.3, **kwargs)
        self.prompt_template = get_prompt_template("skim")
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        对文档进行快速略读
        
        Args:
            input_data: 包含document_content和document_type
            context: 上下文信息
            
        Returns:
            略读结果
        """
        start_time = time.time()
        
        try:
            # 验证输入
            if not self.validate_input(input_data):
                raise ValueError("Invalid input data")
            
            document_content = input_data["document_content"]
            document_type = input_data.get("document_type", "未知类型")
            
            # 如果文档太长，只取前面部分进行略读
            max_length = 8000  # 约2000个token
            if len(document_content) > max_length:
                document_content = document_content[:max_length] + "\n\n[文档内容已截断...]"
            
            # 构建提示词
            prompt = self.prompt_template.format(
                document_content=document_content,
                document_type=document_type
            )
            
            # 调用LLM
            messages = [
                SystemMessage(content="你是一位专业的文档分析专家，擅长快速理解文档要点。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.agenerate([messages])
            result_text = response.generations[0][0].text
            
            # 解析JSON结果
            try:
                # 处理可能包含 markdown 代码块的响应
                json_text = result_text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:]  # 移除 ```json
                if json_text.startswith("```"):
                    json_text = json_text[3:]  # 移除 ```
                if json_text.endswith("```"):
                    json_text = json_text[:-3]  # 移除尾部的 ```
                json_text = json_text.strip()
                
                skim_result = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {result_text}")
                logger.error(f"JSON decode error: {str(e)}")
                # 返回原始文本作为后备
                skim_result = {
                    "document_type": document_type,
                    "core_topic": "解析失败，请查看原始响应",
                    "raw_response": result_text
                }
            
            # 计算token使用量（估算）
            tokens_used = len(prompt) // 4 + len(result_text) // 4
            
            # 记录性能指标
            end_time = time.time()
            self.log_metrics(start_time, end_time, tokens_used, True)
            
            # 更新上下文
            if context:
                context = self.update_context(context, {
                    "skim_result": skim_result,
                    "skim_completed": True
                })
            
            return {
                "success": True,
                "result": skim_result,
                "metadata": {
                    "agent": self.name,
                    "duration": end_time - start_time,
                    "tokens_used": tokens_used,
                    "document_truncated": len(input_data["document_content"]) > max_length
                }
            }
            
        except Exception as e:
            logger.error(f"Error in SkimmerAgent: {str(e)}", exc_info=True)
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
        
        return True