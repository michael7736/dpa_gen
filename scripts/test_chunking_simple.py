#!/usr/bin/env python3
"""
简化的分块策略测试
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.chunking import BaseChunker, ChunkingConfig, ChunkingStrategy
from src.models.chunk import Chunk as DocumentChunk
from src.core.document.hybrid_chunker import HybridChunker, HybridChunkingConfig


# 测试文本
TEST_TEXT = """
# 深度学习技术概述

## 1. 引言

深度学习是机器学习的一个重要分支，它通过模拟人脑神经网络的结构和功能来实现智能计算。近年来，深度学习在计算机视觉、自然语言处理、语音识别等领域取得了突破性进展。

## 2. 核心技术

### 2.1 神经网络基础

神经网络由多层神经元组成，每一层都对输入数据进行特征提取和变换。关键组成部分包括：

- **输入层**：接收原始数据
- **隐藏层**：进行特征学习和转换
- **输出层**：生成最终预测结果

重要发现：研究表明，增加网络深度可以显著提升模型的表达能力，但同时也带来了梯度消失等挑战。

### 2.2 卷积神经网络（CNN）

CNN是处理图像数据的核心技术。其主要创新点在于：

1. **局部感受野**：每个神经元只关注输入的局部区域
2. **权值共享**：同一卷积核在整个图像上共享参数
3. **池化操作**：降低特征图的空间维度

关键优势：CNN能够自动学习图像的层次化特征表示，从低层的边缘检测到高层的物体识别。

### 2.3 循环神经网络（RNN）

RNN专门用于处理序列数据，如文本和时间序列。其特点包括：

- 具有记忆功能，能够保存之前的信息
- 参数在时间步之间共享
- 适合处理变长序列

然而，传统RNN存在长期依赖问题。为此，研究者提出了LSTM和GRU等改进结构。

## 3. 应用领域

深度学习的应用已经渗透到各个领域：

### 3.1 计算机视觉
- 图像分类：识别图像中的物体类别
- 目标检测：定位图像中的物体位置
- 图像分割：像素级的物体识别

### 3.2 自然语言处理
- 机器翻译：自动翻译不同语言
- 情感分析：理解文本的情感倾向
- 问答系统：回答用户的自然语言问题

### 3.3 其他应用
- 推荐系统：个性化内容推荐
- 自动驾驶：环境感知和决策
- 医疗诊断：疾病检测和预测

## 4. 未来展望

深度学习的未来发展方向包括：

首先，模型效率的提升。研究者正在探索如何用更少的参数和计算资源达到相同的性能。

其次，可解释性的增强。理解深度学习模型的决策过程对于关键应用至关重要。

最后，小样本学习能力。减少对大规模标注数据的依赖是实现通用人工智能的关键。

## 5. 结论

深度学习已经成为人工智能领域的核心技术，推动了许多突破性应用的诞生。随着技术的不断进步，我们可以期待深度学习在更多领域创造价值，为人类社会带来更多便利。

总结要点：
1. 深度学习通过多层神经网络实现复杂的模式识别
2. CNN和RNN是两种最重要的网络架构
3. 应用领域广泛，从视觉到语言处理
4. 未来发展注重效率、可解释性和泛化能力
"""


class SimpleFixedChunker(BaseChunker):
    """简化的固定大小分块器"""
    
    async def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # 尝试在句子边界结束
            if end < len(text):
                for punct in ['。', '！', '？', '.', '!', '?']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct > start + chunk_size * 0.8:
                        end = last_punct + 1
                        break
            
            content = text[start:end].strip()
            if content:
                chunk = DocumentChunk(
                    id=str(chunk_index),
                    document_id="test_doc",
                    content=content,
                    content_hash="",
                    start_char=start,
                    end_char=end,
                    chunk_index=chunk_index,
                    char_count=len(content)
                )
                chunks.append(chunk)
                chunk_index += 1
            
            start = end - overlap if overlap > 0 else end
        
        return chunks


class SimpleSemanticChunker(BaseChunker):
    """简化的语义分块器（基于段落）"""
    
    async def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        chunks = []
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # 如果当前块加上新段落超过限制，先保存当前块
            if current_size + para_size > self.config.chunk_size and current_chunk:
                content = '\n\n'.join(current_chunk)
                chunk = DocumentChunk(
                    id=str(chunk_index),
                    document_id="test_doc",
                    content=content,
                    content_hash="",
                    start_char=0,  # 简化处理
                    end_char=len(content),
                    chunk_index=chunk_index,
                    char_count=len(content)
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 开始新块
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # 保存最后一块
        if current_chunk:
            content = '\n\n'.join(current_chunk)
            chunk = DocumentChunk(
                id=str(chunk_index),
                document_id="test_doc",
                content=content,
                content_hash="",
                start_char=0,
                end_char=len(content),
                chunk_index=chunk_index,
                char_count=len(content)
            )
            chunks.append(chunk)
        
        return chunks


class SimpleHybridChunker(HybridChunker):
    """简化的混合分块器"""
    
    def __init__(self, config: HybridChunkingConfig):
        # 跳过复杂的初始化
        self.config = config
        self.encoding = None
        self.vector_store = None
        self._cache = {}
        self.key_info_patterns = []
    
    async def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """简化的混合分块实现"""
        chunks = []
        
        # 1. 识别章节结构
        sections = self._identify_sections(text)
        
        # 2. 对每个章节进行智能分块
        chunk_index = 0
        for section_title, section_content, is_key_section in sections:
            # 根据内容类型选择分块策略
            if len(section_content) < 300:
                # 短章节作为一个块
                chunk = self._create_simple_chunk(
                    section_content, chunk_index, 
                    metadata={"section": section_title, "is_key": is_key_section}
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # 长章节进行细分
                sub_chunks = self._split_long_section(section_content, section_title, is_key_section)
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_index = chunk_index
                    chunks.append(sub_chunk)
                    chunk_index += 1
        
        # 3. 添加滑动窗口块（如果启用）
        if self.config.enable_sliding_windows:
            sliding_chunks = self._create_simple_sliding_windows(text, chunk_index)
            chunks.extend(sliding_chunks)
        
        return chunks
    
    def _identify_sections(self, text: str) -> List[tuple]:
        """识别文本中的章节"""
        sections = []
        
        # 简单的章节识别
        lines = text.split('\n')
        current_section = []
        current_title = "开始"
        is_key = False
        
        for line in lines:
            # 检查是否是标题
            if line.startswith('#'):
                # 保存之前的章节
                if current_section:
                    content = '\n'.join(current_section).strip()
                    if content:
                        sections.append((current_title, content, is_key))
                
                # 开始新章节
                current_title = line.strip('#').strip()
                current_section = []
                
                # 检查是否是关键章节
                is_key = any(keyword in current_title.lower() 
                           for keyword in ['结论', '总结', '核心', '关键', '重要'])
            else:
                current_section.append(line)
        
        # 保存最后一个章节
        if current_section:
            content = '\n'.join(current_section).strip()
            if content:
                sections.append((current_title, content, is_key))
        
        return sections
    
    def _create_simple_chunk(self, content: str, index: int, metadata: Dict = None) -> DocumentChunk:
        """创建简单的块"""
        chunk_metadata = metadata or {}
        chunk_metadata.update({
            "chunk_type": "section",
            "strategy": "hybrid"
        })
        
        return DocumentChunk(
            id=str(index),
            document_id="test_doc",
            content=content.strip(),
            content_hash="",
            start_char=0,
            end_char=len(content),
            chunk_index=index,
            char_count=len(content),
            metadata=chunk_metadata
        )
    
    def _split_long_section(self, content: str, section_title: str, is_key: bool) -> List[DocumentChunk]:
        """分割长章节"""
        chunks = []
        
        # 按段落分割
        paragraphs = content.split('\n\n')
        current_chunk_text = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检查是否应该开始新块
            if current_size + len(para) > self.config.chunk_size and current_chunk_text:
                chunk_content = '\n\n'.join(current_chunk_text)
                chunk = self._create_simple_chunk(
                    chunk_content, 0,
                    metadata={
                        "section": section_title,
                        "is_key": is_key,
                        "chunk_type": "paragraph_group"
                    }
                )
                chunks.append(chunk)
                
                current_chunk_text = [para]
                current_size = len(para)
            else:
                current_chunk_text.append(para)
                current_size += len(para)
        
        # 保存最后一块
        if current_chunk_text:
            chunk_content = '\n\n'.join(current_chunk_text)
            chunk = self._create_simple_chunk(
                chunk_content, 0,
                metadata={
                    "section": section_title,
                    "is_key": is_key,
                    "chunk_type": "paragraph_group"
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_simple_sliding_windows(self, text: str, start_index: int) -> List[DocumentChunk]:
        """创建简单的滑动窗口"""
        chunks = []
        window_size = int(self.config.chunk_size * 0.8)  # 稍小的窗口
        step = int(window_size * 0.5)  # 50%重叠
        
        for i in range(0, len(text) - window_size, step):
            window_text = text[i:i + window_size]
            
            # 调整到句子边界
            last_period = window_text.rfind('。')
            if last_period > window_size * 0.7:
                window_text = window_text[:last_period + 1]
            
            chunk = DocumentChunk(
                id=str(start_index + len(chunks)),
                document_id="test_doc",
                content=window_text.strip(),
                content_hash="",
                start_char=i,
                end_char=i + len(window_text),
                chunk_index=start_index + len(chunks),
                char_count=len(window_text),
                metadata={"chunk_type": "sliding_window"}
            )
            chunks.append(chunk)
        
        return chunks


async def test_chunking_strategies():
    """测试不同的分块策略"""
    results = {}
    
    # 配置
    chunk_size = 500
    chunk_overlap = 100
    
    # 1. 测试固定大小分块
    print("\n=== 测试固定大小分块 ===")
    config = ChunkingConfig(
        strategy=ChunkingStrategy.FIXED_SIZE,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    fixed_chunker = SimpleFixedChunker(config)
    fixed_chunks = await fixed_chunker.chunk_text(TEST_TEXT)
    
    print(f"生成块数: {len(fixed_chunks)}")
    print(f"平均块大小: {sum(c.char_count for c in fixed_chunks) / len(fixed_chunks):.1f}")
    results["fixed_size"] = analyze_chunks(fixed_chunks)
    
    # 2. 测试语义分块
    print("\n=== 测试语义分块 ===")
    config = ChunkingConfig(
        strategy=ChunkingStrategy.SEMANTIC,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    semantic_chunker = SimpleSemanticChunker(config)
    semantic_chunks = await semantic_chunker.chunk_text(TEST_TEXT)
    
    print(f"生成块数: {len(semantic_chunks)}")
    print(f"平均块大小: {sum(c.char_count for c in semantic_chunks) / len(semantic_chunks):.1f}")
    results["semantic"] = analyze_chunks(semantic_chunks)
    
    # 3. 测试混合分块
    print("\n=== 测试混合分块 ===")
    hybrid_config = HybridChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        enable_sliding_windows=True,
        enable_key_info_extraction=True,
        use_embeddings=False  # 禁用向量化以简化测试
    )
    hybrid_chunker = SimpleHybridChunker(hybrid_config)
    hybrid_chunks = await hybrid_chunker.chunk_text(TEST_TEXT)
    
    print(f"生成块数: {len(hybrid_chunks)}")
    print(f"平均块大小: {sum(c.char_count for c in hybrid_chunks) / len(hybrid_chunks):.1f}")
    
    # 分析块类型
    chunk_types = {}
    key_chunks = 0
    for chunk in hybrid_chunks:
        if hasattr(chunk, 'metadata') and chunk.metadata:
            chunk_type = chunk.metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            if chunk.metadata.get('is_key', False):
                key_chunks += 1
    
    print(f"块类型分布: {chunk_types}")
    print(f"关键块数量: {key_chunks}")
    
    results["hybrid"] = analyze_chunks(hybrid_chunks)
    
    # 4. 比较结果
    print("\n=== 策略比较 ===")
    print_comparison(results)
    
    return results


def analyze_chunks(chunks: List[DocumentChunk]) -> Dict[str, Any]:
    """分析分块结果"""
    if not chunks:
        return {"error": "No chunks"}
    
    sizes = [c.char_count for c in chunks]
    
    analysis = {
        "count": len(chunks),
        "avg_size": sum(sizes) / len(sizes),
        "min_size": min(sizes),
        "max_size": max(sizes),
        "std_dev": (sum((s - sum(sizes)/len(sizes))**2 for s in sizes) / len(sizes))**0.5
    }
    
    # 分析块类型
    if any(hasattr(c, 'metadata') and c.metadata for c in chunks):
        chunk_types = {}
        for chunk in chunks:
            if hasattr(chunk, 'metadata') and chunk.metadata:
                chunk_type = chunk.metadata.get('chunk_type', 'default')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        analysis["chunk_types"] = chunk_types
    
    return analysis


def print_comparison(results: Dict[str, Dict[str, Any]]):
    """打印策略比较"""
    strategies = list(results.keys())
    
    # 比较块数量
    print("\n块数量:")
    for strategy in strategies:
        if "error" not in results[strategy]:
            print(f"  {strategy}: {results[strategy]['count']}")
    
    # 比较平均大小
    print("\n平均块大小:")
    for strategy in strategies:
        if "error" not in results[strategy]:
            print(f"  {strategy}: {results[strategy]['avg_size']:.1f}")
    
    # 比较大小分布
    print("\n大小标准差（一致性）:")
    for strategy in strategies:
        if "error" not in results[strategy]:
            print(f"  {strategy}: {results[strategy]['std_dev']:.1f}")
    
    # 评分
    print("\n综合评分（基于多个因素）:")
    for strategy in strategies:
        if "error" not in results[strategy]:
            score = calculate_score(results[strategy])
            print(f"  {strategy}: {score:.1f}/100")


def calculate_score(analysis: Dict[str, Any]) -> float:
    """计算策略得分"""
    score = 0.0
    
    # 块大小合理性（300-600最佳）
    avg_size = analysis['avg_size']
    if 300 <= avg_size <= 600:
        score += 30
    elif 200 <= avg_size <= 700:
        score += 20
    else:
        score += 10
    
    # 大小一致性（标准差越小越好）
    std_dev = analysis['std_dev']
    if std_dev < 100:
        score += 20
    elif std_dev < 200:
        score += 15
    else:
        score += 5
    
    # 块数量合理性
    count = analysis['count']
    if 5 <= count <= 20:
        score += 20
    elif 3 <= count <= 30:
        score += 10
    
    # 块类型多样性（仅适用于混合策略）
    if 'chunk_types' in analysis and len(analysis['chunk_types']) > 1:
        score += 20
    
    # 其他因素
    score += 10  # 基础分
    
    return min(score, 100)


async def test_retrieval_scenarios():
    """测试检索场景"""
    print("\n\n=== 测试检索场景 ===")
    
    # 创建混合分块器
    hybrid_config = HybridChunkingConfig(
        chunk_size=400,
        chunk_overlap=100,
        enable_sliding_windows=True,
        use_embeddings=False
    )
    chunker = SimpleHybridChunker(hybrid_config)
    chunks = await chunker.chunk_text(TEST_TEXT)
    
    # 测试查询
    test_queries = [
        "深度学习的核心技术",
        "CNN的主要创新点",
        "RNN的特点",
        "深度学习的应用领域",
        "未来发展方向"
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        relevant_chunks = find_relevant_chunks(chunks, query)
        print(f"找到 {len(relevant_chunks)} 个相关块")
        
        if relevant_chunks:
            best = relevant_chunks[0]
            print(f"最佳匹配: {best.content[:100]}...")
            if hasattr(best, 'metadata') and best.metadata:
                print(f"块类型: {best.metadata.get('chunk_type', 'unknown')}")


def find_relevant_chunks(chunks: List[DocumentChunk], query: str) -> List[DocumentChunk]:
    """简单的关键词匹配"""
    query_words = set(query.lower().split())
    scored_chunks = []
    
    for chunk in chunks:
        content_lower = chunk.content.lower()
        # 计算匹配分数
        score = sum(1 for word in query_words if word in content_lower)
        
        # 如果是关键块，增加权重
        if hasattr(chunk, 'metadata') and chunk.metadata and chunk.metadata.get('is_key', False):
            score *= 1.5
        
        if score > 0:
            scored_chunks.append((score, chunk))
    
    # 按分数排序
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    return [chunk for score, chunk in scored_chunks[:3]]


async def main():
    """主函数"""
    print("=== 文档分块策略优化测试 ===")
    
    # 运行测试
    results = await test_chunking_strategies()
    
    # 测试检索场景
    await test_retrieval_scenarios()
    
    # 保存结果
    output_file = Path("chunking_test_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        # 转换结果为可序列化格式
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                serializable_results[key] = {
                    k: v for k, v in value.items()
                    if not k.startswith('_')
                }
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")
    
    # 打印优化建议
    print("\n=== 优化建议 ===")
    print("1. 混合策略在保持合理块大小的同时，提供了更好的检索覆盖")
    print("2. 滑动窗口可以提高相关内容的命中率")
    print("3. 识别关键章节有助于提升重要信息的检索权重")
    print("4. 建议根据文档类型动态调整分块参数")


if __name__ == "__main__":
    asyncio.run(main())