"""
Base Agent for AAG System
所有Agent的基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from ...config.settings import get_settings
from ...utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    """AAG Agent基类"""
    
    def __init__(
        self,
        name: str,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        callbacks: Optional[List] = None
    ):
        """
        初始化Agent
        
        Args:
            name: Agent名称
            model_name: 使用的模型名称
            temperature: 温度参数
            callbacks: 回调函数列表
        """
        self.name = name
        self.model_name = model_name or settings.ai_model.default_llm_model
        self.temperature = temperature
        self.callbacks = callbacks or []
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=temperature,
            openai_api_key=settings.ai_model.openai_api_key,
            base_url=settings.ai_model.openai_base_url,
            callbacks=self.callbacks
        )
        
        logger.info(f"Initialized {self.name} with model {self.model_name}")
    
    @abstractmethod
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            处理结果
        """
        pass
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            是否有效
        """
        return True
    
    def update_context(
        self,
        context: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新上下文
        
        Args:
            context: 当前上下文
            new_data: 新数据
            
        Returns:
            更新后的上下文
        """
        if context is None:
            context = {}
        
        context.update(new_data)
        context["last_agent"] = self.name
        
        return context
    
    def log_metrics(
        self,
        start_time: float,
        end_time: float,
        tokens_used: int,
        success: bool
    ):
        """记录性能指标"""
        duration = end_time - start_time
        logger.info(
            f"{self.name} execution metrics: "
            f"duration={duration:.2f}s, "
            f"tokens={tokens_used}, "
            f"success={success}"
        )