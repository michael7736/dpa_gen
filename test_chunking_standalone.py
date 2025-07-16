#!/usr/bin/env python3
"""
独立的分块策略测试脚本
"""

import asyncio
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re


@dataclass
class SimpleChunk:
    """简单的块数据结构"""
    id: str
    content: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]


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

## 4. 未来展望

深度学习的未来发展方向包括：

首先，模型效率的提升。研究者正在探索如何用更少的参数和计算资源达到相同的性能。

其次，可解释性的增强。理解深度学习模型的决策过程对于关键应用至关重要。

最后，小样本学习能力。减少对大规模标注数据的依赖是实现通用人工智能的关键。

## 5. 结论

深度学习已经成为人工智能领域的核心技术，推动了许多突破性应用的诞生。随着技术的不断进步，我们可以期待深度学习在更多领域创造价值。

总结要点：
1. 深度学习通过多层神经网络实现复杂的模式识别
2. CNN和RNN是两种最重要的网络架构
3. 应用领域广泛，从视觉到语言处理
4. 未来发展注重效率、可解释性和泛化能力
"""


def fixed_size_chunking(text: str, chunk_size: int = 500, overlap: int = 100) -> List[SimpleChunk]:
    """固定大小分块"""
    chunks = []
    start = 0
    chunk_id = 0
    
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
            chunk = SimpleChunk(
                id=f"fixed_{chunk_id}",
                content=content,
                start_pos=start,
                end_pos=end,
                metadata={"type": "fixed", "size": len(content)}
            )
            chunks.append(chunk)
            chunk_id += 1
        
        start = end - overlap if overlap > 0 and end > start + overlap else end
    
    return chunks


def semantic_chunking(text: str, max_size: int = 500) -> List[SimpleChunk]:
    """语义分块（基于段落）"""
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = []
    current_size = 0
    chunk_id = 0
    start_pos = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_size = len(para)
        
        if current_size + para_size > max_size and current_chunk:
            # 保存当前块
            content = '\n\n'.join(current_chunk)
            chunk = SimpleChunk(
                id=f"semantic_{chunk_id}",
                content=content,
                start_pos=start_pos,
                end_pos=start_pos + len(content),
                metadata={"type": "semantic", "paragraphs": len(current_chunk)}
            )
            chunks.append(chunk)
            chunk_id += 1
            
            # 开始新块
            start_pos = text.find(para, start_pos + len(content))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # 保存最后一块
    if current_chunk:
        content = '\n\n'.join(current_chunk)
        chunk = SimpleChunk(
            id=f"semantic_{chunk_id}",
            content=content,
            start_pos=start_pos,
            end_pos=start_pos + len(content),
            metadata={"type": "semantic", "paragraphs": len(current_chunk)}
        )
        chunks.append(chunk)
    
    return chunks


def hybrid_chunking(text: str, base_size: int = 400) -> List[SimpleChunk]:
    """混合分块策略"""
    chunks = []
    chunk_id = 0
    
    # 1. 识别章节
    sections = []
    lines = text.split('\n')
    current_section = []
    current_title = ""
    section_start = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            # 保存之前的章节
            if current_section:
                content = '\n'.join(current_section)
                sections.append({
                    'title': current_title,
                    'content': content,
                    'start': section_start,
                    'is_key': any(k in current_title.lower() for k in ['结论', '总结', '核心', '关键'])
                })
            
            # 开始新章节
            current_title = line.strip('#').strip()
            current_section = []
            section_start = text.find(line)
        else:
            current_section.append(line)
    
    # 保存最后一个章节
    if current_section:
        content = '\n'.join(current_section)
        sections.append({
            'title': current_title,
            'content': content,
            'start': section_start,
            'is_key': any(k in current_title.lower() for k in ['结论', '总结', '核心', '关键'])
        })
    
    # 2. 对每个章节进行智能分块
    for section in sections:
        section_content = section['content'].strip()
        
        if not section_content:
            continue
        
        # 短章节作为一个块
        if len(section_content) < base_size:
            chunk = SimpleChunk(
                id=f"hybrid_{chunk_id}",
                content=section_content,
                start_pos=section['start'],
                end_pos=section['start'] + len(section_content),
                metadata={
                    "type": "section",
                    "title": section['title'],
                    "is_key": section['is_key']
                }
            )
            chunks.append(chunk)
            chunk_id += 1
        else:
            # 长章节按段落分割
            paragraphs = section_content.split('\n\n')
            current_chunk = []
            current_size = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                if current_size + len(para) > base_size and current_chunk:
                    content = '\n\n'.join(current_chunk)
                    chunk = SimpleChunk(
                        id=f"hybrid_{chunk_id}",
                        content=content,
                        start_pos=section['start'],
                        end_pos=section['start'] + len(content),
                        metadata={
                            "type": "section_part",
                            "title": section['title'],
                            "is_key": section['is_key']
                        }
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                    
                    current_chunk = [para]
                    current_size = len(para)
                else:
                    current_chunk.append(para)
                    current_size += len(para)
            
            # 保存最后的内容
            if current_chunk:
                content = '\n\n'.join(current_chunk)
                chunk = SimpleChunk(
                    id=f"hybrid_{chunk_id}",
                    content=content,
                    start_pos=section['start'],
                    end_pos=section['start'] + len(content),
                    metadata={
                        "type": "section_part",
                        "title": section['title'],
                        "is_key": section['is_key']
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
    
    # 3. 添加滑动窗口（提高检索覆盖）
    window_size = int(base_size * 0.8)
    step = int(window_size * 0.5)
    
    for i in range(0, len(text) - window_size, step):
        window_text = text[i:i + window_size]
        
        # 调整到句子边界
        last_period = window_text.rfind('。')
        if last_period > window_size * 0.7:
            window_text = window_text[:last_period + 1]
        
        chunk = SimpleChunk(
            id=f"hybrid_window_{chunk_id}",
            content=window_text.strip(),
            start_pos=i,
            end_pos=i + len(window_text),
            metadata={"type": "sliding_window"}
        )
        chunks.append(chunk)
        chunk_id += 1
    
    return chunks


def analyze_chunks(chunks: List[SimpleChunk]) -> Dict[str, Any]:
    """分析分块结果"""
    sizes = [len(c.content) for c in chunks]
    
    analysis = {
        "count": len(chunks),
        "avg_size": sum(sizes) / len(sizes) if sizes else 0,
        "min_size": min(sizes) if sizes else 0,
        "max_size": max(sizes) if sizes else 0,
        "total_chars": sum(sizes)
    }
    
    # 分析块类型
    types = {}
    for chunk in chunks:
        chunk_type = chunk.metadata.get("type", "unknown")
        types[chunk_type] = types.get(chunk_type, 0) + 1
    analysis["types"] = types
    
    # 计算覆盖率
    covered_chars = set()
    for chunk in chunks:
        for i in range(chunk.start_pos, chunk.end_pos):
            covered_chars.add(i)
    
    analysis["coverage_ratio"] = len(covered_chars) / len(TEST_TEXT) if TEST_TEXT else 0
    
    return analysis


def test_retrieval(chunks: List[SimpleChunk], query: str) -> List[SimpleChunk]:
    """测试检索效果"""
    query_words = set(query.lower().split())
    scored_chunks = []
    
    for chunk in chunks:
        content_lower = chunk.content.lower()
        
        # 计算匹配分数
        score = 0
        for word in query_words:
            if word in content_lower:
                score += content_lower.count(word)
        
        # 关键块加权
        if chunk.metadata.get("is_key", False):
            score *= 1.5
        
        if score > 0:
            scored_chunks.append((score, chunk))
    
    # 排序并返回前3个
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored_chunks[:3]]


def main():
    """主函数"""
    print("=== 文档分块策略优化测试 ===\n")
    
    # 测试不同策略
    print("开始固定大小分块...")
    fixed_chunks = fixed_size_chunking(TEST_TEXT)
    print(f"固定大小分块完成: {len(fixed_chunks)} 块")
    
    print("\n开始语义分块...")
    semantic_chunks = semantic_chunking(TEST_TEXT)
    print(f"语义分块完成: {len(semantic_chunks)} 块")
    
    print("\n开始混合分块...")
    hybrid_chunks = hybrid_chunking(TEST_TEXT)
    print(f"混合分块完成: {len(hybrid_chunks)} 块")
    
    strategies = {
        "固定大小": fixed_chunks,
        "语义分块": semantic_chunks,
        "混合策略": hybrid_chunks
    }
    
    # 分析结果
    results = {}
    for name, chunks in strategies.items():
        print(f"\n{name}分块结果:")
        analysis = analyze_chunks(chunks)
        results[name] = analysis
        
        print(f"  块数量: {analysis['count']}")
        print(f"  平均大小: {analysis['avg_size']:.1f} 字符")
        print(f"  大小范围: {analysis['min_size']} - {analysis['max_size']}")
        print(f"  覆盖率: {analysis['coverage_ratio']:.1%}")
        if analysis.get('types'):
            print(f"  块类型: {analysis['types']}")
    
    # 测试检索效果
    print("\n\n=== 检索效果测试 ===")
    test_queries = [
        "深度学习核心技术",
        "CNN的创新点",
        "未来发展方向",
        "RNN的特点"
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        
        for name, chunks in strategies.items():
            relevant = test_retrieval(chunks, query)
            print(f"\n  {name} - 找到 {len(relevant)} 个相关块:")
            
            if relevant:
                best = relevant[0]
                preview = best.content[:80].replace('\n', ' ')
                print(f"    最佳匹配: {preview}...")
                if best.metadata.get("is_key"):
                    print(f"    (关键章节)")
    
    # 优化建议
    print("\n\n=== 优化建议 ===")
    
    # 评分
    scores = {}
    for name, analysis in results.items():
        score = 0
        
        # 块大小合理性
        if 300 <= analysis['avg_size'] <= 600:
            score += 30
        
        # 覆盖率
        score += analysis['coverage_ratio'] * 20
        
        # 块数量合理性
        if 10 <= analysis['count'] <= 30:
            score += 20
        
        # 类型多样性
        if len(analysis.get('types', {})) > 1:
            score += 20
        
        scores[name] = score
    
    # 排序并显示
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("\n策略评分（满分100）:")
    for name, score in sorted_scores:
        print(f"  {name}: {score:.1f}分")
    
    best_strategy = sorted_scores[0][0]
    print(f"\n推荐策略: {best_strategy}")
    
    print("\n具体优化建议:")
    print("1. 混合策略结合了结构化分块和滑动窗口，提供最佳检索覆盖")
    print("2. 识别关键章节（如结论、总结）有助于提升重要信息的检索权重")
    print("3. 滑动窗口可以捕获跨段落的相关内容，减少信息遗漏")
    print("4. 建议根据文档类型动态调整块大小：")
    print("   - 技术文档: 400-600字符")
    print("   - 学术论文: 500-700字符")
    print("   - 新闻文章: 300-500字符")
    
    # 保存结果
    with open("chunking_optimization_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "analysis": results,
            "scores": scores,
            "recommendation": best_strategy
        }, f, ensure_ascii=False, indent=2)
    
    print("\n\n结果已保存到: chunking_optimization_results.json")


if __name__ == "__main__":
    main()