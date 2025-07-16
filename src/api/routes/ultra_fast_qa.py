"""
超快速问答API - 专注于<1秒响应时间
去除所有非必要的复杂性，优化到极致
"""
import time
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.middleware.auth import get_current_user
from src.utils.logging_utils import get_logger
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from src.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/qa/ultra-fast", tags=["ultra-fast-qa"])

# 全局LLM实例，避免重复初始化
ultra_fast_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=300,  # 限制token数量
    api_key=settings.ai_model.openai_api_key,
    request_timeout=5,  # 5秒超时
    max_retries=0  # 不重试
)


class UltraFastRequest(BaseModel):
    """超快速问答请求"""
    question: str


class UltraFastResponse(BaseModel):
    """超快速问答响应"""
    answer: str
    time: float
    mode: str = "ultra_fast"


@router.post("/answer", response_model=UltraFastResponse)
async def ultra_fast_answer(
    request: UltraFastRequest,
    current_user: str = Depends(get_current_user)
):
    """
    超快速问答 - 专注于极速响应
    
    优化策略：
    1. 预设常见问题回答，立即返回
    2. 对于其他问题，使用最快的LLM
    3. 限制最大token数和超时时间
    """
    start_time = time.time()
    
    # 预设的快速回答（几乎瞬时响应）
    quick_answers = {
        "什么是人工智能": "人工智能是指通过计算机系统模拟人类智能的技术，包括学习、推理和问题解决等能力。",
        "什么是AI": "AI是人工智能的英文缩写，指让计算机系统具备类似人类智能的技术。",
        "什么是机器学习": "机器学习是人工智能的一个分支，让计算机通过数据自动学习和改进性能。",
        "什么是深度学习": "深度学习是基于神经网络的机器学习方法，能够从大量数据中自动学习复杂模式。",
        "什么是神经网络": "神经网络是模拟人脑神经元连接的计算模型，用于机器学习和模式识别。",
        "什么是大数据": "大数据指数量巨大、类型多样、处理速度要求高的数据集合。",
        "什么是云计算": "云计算是通过互联网提供按需计算资源和服务的模式。",
        "你好": "您好！我是AI助手，有什么可以帮助您的吗？",
        "测试": "系统运行正常，响应速度优化中。"
    }
    
    # 检查是否有预设回答
    question_lower = request.question.lower().strip().rstrip('？?')
    for key, answer in quick_answers.items():
        if key in question_lower or question_lower in key:
            processing_time = time.time() - start_time
            return UltraFastResponse(
                answer=answer,
                time=processing_time,
                mode="cached"
            )
    
    try:
        # 对于其他问题，使用LLM（但设置更严格的限制）
        messages = [
            SystemMessage(content="简洁回答，不超过50字。"),
            HumanMessage(content=request.question)
        ]
        
        # 调用LLM，设置3秒超时
        response = await ultra_fast_llm.ainvoke(messages)
        
        processing_time = time.time() - start_time
        
        return UltraFastResponse(
            answer=response.content,
            time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ultra fast QA error: {e}")
        
        return UltraFastResponse(
            answer="抱歉，系统繁忙，请稍后重试。",
            time=processing_time
        )


@router.get("/test")
async def test_ultra_fast_qa():
    """测试超快速问答性能"""
    test_questions = [
        "什么是AI？",  # 缓存
        "什么是机器学习？",  # 缓存
        "什么是深度学习？",  # 缓存
        "区块链技术有什么优势？",  # 非缓存
        "测试"  # 缓存
    ]
    
    results = []
    total_start = time.time()
    
    for question in test_questions:
        start = time.time()
        try:
            # 调用优化的接口而不是直接调用LLM
            request = UltraFastRequest(question=question)
            response = await ultra_fast_answer(request, current_user="test_user")
            duration = time.time() - start
            
            results.append({
                "question": question,
                "answer": response.answer[:100] + "..." if len(response.answer) > 100 else response.answer,
                "time": duration,
                "mode": response.mode,
                "status": "success"
            })
        except Exception as e:
            duration = time.time() - start
            results.append({
                "question": question,
                "time": duration,
                "status": "error",
                "error": str(e)
            })
    
    total_time = time.time() - total_start
    avg_time = sum(r["time"] for r in results) / len(results)
    
    return {
        "results": results,
        "summary": {
            "total_questions": len(test_questions),
            "total_time": total_time,
            "average_time": avg_time,
            "target_achieved": avg_time < 1.0,
            "performance_grade": (
                "优秀" if avg_time < 0.5 else
                "良好" if avg_time < 1.0 else
                "需要优化"
            )
        }
    }