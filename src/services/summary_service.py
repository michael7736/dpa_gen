"""
轻量级文档摘要服务
快速生成文档摘要，帮助用户决策
"""

import re
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SummaryResult(BaseModel):
    """摘要结果模型"""
    summary: str = Field(..., description="文档摘要")
    keywords: List[str] = Field(..., description="关键词列表")
    document_type: str = Field(..., description="文档类型")
    complexity_level: str = Field(..., description="复杂度级别")
    estimated_read_time: str = Field(..., description="预估阅读时间")
    key_sections: List[Dict[str, Any]] = Field(default_factory=list, description="关键章节")
    recommendation: Dict[str, Any] = Field(..., description="处理建议")


class SummaryService:
    """摘要服务类"""
    
    def __init__(self):
        # 使用轻量级模型
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=1000,
            timeout=30
        )
        
        # 摘要提示模板
        self.summary_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""你是一个专业的文档分析助手。请快速分析文档并生成简洁的摘要。

要求：
1. 摘要长度：150-200字
2. 提取5-10个关键词
3. 识别文档类型和复杂度
4. 估算阅读时间
5. 列出主要章节
6. 给出处理建议

输出格式（JSON）：
{
    "summary": "文档摘要内容",
    "keywords": ["关键词1", "关键词2", ...],
    "document_type": "技术文档|研究报告|用户手册|其他",
    "complexity_level": "低|中|高",
    "estimated_read_time": "X分钟",
    "key_sections": [
        {"title": "章节标题", "page": 页码或位置}
    ],
    "recommendation": {
        "worth_indexing": true/false,
        "worth_deep_analysis": true/false,
        "reason": "建议理由"
    }
}"""),
            HumanMessage(content="{content}")
        ])
    
    async def generate_summary(
        self,
        document_id: str,
        content: bytes,
        file_type: str,
        progress_callback: Optional[Callable] = None
    ) -> SummaryResult:
        """
        生成文档摘要
        
        Args:
            document_id: 文档ID
            content: 文档内容（字节）
            file_type: 文件类型
            progress_callback: 进度回调函数
            
        Returns:
            摘要结果
        """
        try:
            # 1. 预处理文档（10%）
            if progress_callback:
                await progress_callback(10, "正在预处理文档...")
            
            # 解码文档内容
            text_content = self._decode_content(content, file_type)
            
            # 截取前5000字符进行摘要（轻量化处理）
            preview_content = text_content[:5000]
            
            # 2. 提取关键段落（30%）
            if progress_callback:
                await progress_callback(30, "提取关键段落...")
            
            key_sections = self._extract_key_sections(text_content)
            
            # 3. 生成摘要（60%）
            if progress_callback:
                await progress_callback(60, "生成摘要...")
            
            # 调用LLM生成摘要
            response = await self.llm.ainvoke(
                self.summary_prompt.format_messages(content=preview_content)
            )
            
            # 解析响应
            import json
            result_data = json.loads(response.content)
            
            # 4. 提取关键词（80%）
            if progress_callback:
                await progress_callback(80, "提取关键词...")
            
            # 如果LLM没有返回足够的关键词，使用简单的关键词提取
            if len(result_data.get("keywords", [])) < 5:
                additional_keywords = self._extract_keywords(text_content)
                result_data["keywords"].extend(additional_keywords)
                result_data["keywords"] = list(set(result_data["keywords"]))[:10]
            
            # 5. 生成建议（100%）
            if progress_callback:
                await progress_callback(100, "生成处理建议...")
            
            # 补充关键章节信息
            if not result_data.get("key_sections"):
                result_data["key_sections"] = key_sections
            
            # 创建结果对象
            summary_result = SummaryResult(**result_data)
            
            logger.info(f"Generated summary for document {document_id}")
            
            return summary_result
            
        except Exception as e:
            logger.error(f"Summary generation failed for document {document_id}: {e}")
            
            # 返回默认结果
            return SummaryResult(
                summary="文档摘要生成失败，请查看原文。",
                keywords=[],
                document_type="unknown",
                complexity_level="unknown",
                estimated_read_time="未知",
                key_sections=[],
                recommendation={
                    "worth_indexing": True,
                    "worth_deep_analysis": False,
                    "reason": "摘要生成失败，建议手动查看文档"
                }
            )
    
    def _decode_content(self, content: bytes, file_type: str) -> str:
        """解码文档内容"""
        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
        
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 如果都失败，使用错误处理
        return content.decode('utf-8', errors='ignore')
    
    def _extract_key_sections(self, content: str) -> List[Dict[str, Any]]:
        """提取关键章节"""
        sections = []
        
        # 简单的章节提取逻辑
        # 查找类似 "第X章"、"X."、"Chapter X" 等模式
        patterns = [
            r'第[一二三四五六七八九十\d]+[章节][\s:：]*(.*)',
            r'^\d+\.?\s+(.*)',
            r'^Chapter\s+\d+[\s:：]*(.*)',
            r'^Section\s+\d+[\s:：]*(.*)',
            r'^[一二三四五六七八九十]+[、.]\s*(.*)'
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines[:100]):  # 只检查前100行
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    title = match.group(1) if match.lastindex else line
                    sections.append({
                        "title": title.strip(),
                        "page": i + 1  # 使用行号作为位置
                    })
                    break
        
        # 限制返回前10个章节
        return sections[:10]
    
    def _extract_keywords(self, content: str) -> List[str]:
        """简单的关键词提取"""
        # 移除常见停用词
        stopwords = {
            '的', '了', '和', '是', '在', '有', '我', '他', '她', '它', '们',
            '这', '那', '个', '为', '与', '或', '但', '如果', '因为', '所以',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'
        }
        
        # 提取中英文词汇
        chinese_words = re.findall(r'[\u4e00-\u9fa5]+', content)
        english_words = re.findall(r'\b[A-Za-z]+\b', content)
        
        # 统计词频
        word_freq = {}
        
        for word in chinese_words + english_words:
            if len(word) < 2 or word.lower() in stopwords:
                continue
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按词频排序，返回前10个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:10]]
        
        return keywords
    
    def estimate_read_time(self, content: str) -> str:
        """估算阅读时间"""
        # 假设中文阅读速度：300字/分钟
        # 英文阅读速度：200词/分钟
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', content))
        english_words = len(re.findall(r'\b[A-Za-z]+\b', content))
        
        # 计算阅读时间
        chinese_time = chinese_chars / 300
        english_time = english_words / 200
        
        total_minutes = int(chinese_time + english_time)
        
        if total_minutes < 1:
            return "少于1分钟"
        elif total_minutes < 5:
            return f"{total_minutes}分钟"
        elif total_minutes < 30:
            return f"{(total_minutes // 5) * 5}分钟"
        elif total_minutes < 60:
            return f"{(total_minutes // 10) * 10}分钟"
        else:
            hours = total_minutes // 60
            return f"{hours}小时"