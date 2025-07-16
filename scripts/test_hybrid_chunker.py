#!/usr/bin/env python3
"""
测试混合分块器效果
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from src.core.chunking import ChunkingStrategy, document_chunker
from src.core.document.hybrid_chunker import create_hybrid_chunker
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文本样本
TEST_DOCUMENTS = {
    "technical_doc": """
# 深度学习技术文档

## 1. 概述

深度学习是机器学习的一个分支，它基于人工神经网络的学习算法。深度学习模型能够学习数据的多层表示，从而实现复杂的模式识别任务。

### 1.1 关键概念

深度学习的核心概念包括：
- **神经网络**：由多层神经元组成的计算模型
- **反向传播**：用于训练神经网络的核心算法
- **梯度下降**：优化网络参数的方法

## 2. 主要技术

### 2.1 卷积神经网络（CNN）

卷积神经网络主要用于图像识别任务。CNN的主要组件包括：

1. **卷积层**：提取局部特征
2. **池化层**：降低特征维度
3. **全连接层**：进行最终分类

重要发现：研究表明，深层CNN能够学习层次化的特征表示，从低层的边缘检测到高层的物体识别。

### 2.2 循环神经网络（RNN）

RNN专门处理序列数据，如文本和时间序列。主要变体包括：

- LSTM（长短期记忆网络）
- GRU（门控循环单元）

关键优势：RNN能够保持序列中的长期依赖关系，这对于自然语言处理任务至关重要。

## 3. 应用领域

深度学习在多个领域取得了突破性进展：

1. **计算机视觉**
   - 图像分类
   - 目标检测
   - 图像分割

2. **自然语言处理**
   - 机器翻译
   - 情感分析
   - 文本生成

3. **语音识别**
   - 语音转文字
   - 说话人识别

## 4. 总结与展望

深度学习已经成为人工智能领域最重要的技术之一。未来的发展方向包括：

- **模型压缩**：使深度学习模型能够在移动设备上运行
- **可解释性**：提高模型决策的透明度
- **小样本学习**：减少对大量标注数据的依赖

结论：深度学习技术将继续推动人工智能的发展，在更多领域创造价值。
""",
    
    "research_paper": """
人工智能在教育领域的应用研究

摘要：本研究探讨了人工智能技术在现代教育中的应用及其影响。通过对500名学生的实验研究，我们发现AI辅助学习系统能够显著提高学习效率。

1. 引言

教育是社会发展的基石。随着人工智能技术的快速发展，教育领域正经历着深刻的变革。本研究旨在评估AI技术对学生学习成效的影响。

2. 研究方法

我们采用了混合研究方法：
- 定量分析：对比实验组和对照组的学习成绩
- 定性分析：通过访谈了解学生的学习体验

实验设计：
(1) 实验组使用AI辅助学习系统
(2) 对照组采用传统学习方法
(3) 实验周期为3个月

3. 研究发现

3.1 学习成效提升

关键发现：使用AI系统的学生平均成绩提高了32%。具体表现在：
- 数学成绩提升35%
- 语言学习效率提高28%
- 科学理解能力增强30%

3.2 个性化学习

重要观察：AI系统能够根据每个学生的学习进度和风格调整教学内容。这种个性化方法特别有助于：
- 学习困难学生的进步
- 优秀学生的深度学习

4. 讨论

研究结果表明，AI在教育中的应用潜力巨大。然而，我们也需要注意以下挑战：

首先，技术依赖问题。过度依赖AI可能影响学生的独立思考能力。
其次，数据隐私保护。学生的学习数据需要得到妥善保护。
最后，教师角色转变。教师需要适应新的教学模式。

5. 结论与建议

综上所述，人工智能技术在教育领域具有广阔的应用前景。我们建议：

1. 逐步推广AI辅助教学系统
2. 加强教师培训，帮助他们掌握新技术
3. 制定数据保护政策，确保学生隐私安全
4. 持续研究AI对教育长期影响

本研究为教育技术的发展提供了重要参考，未来需要更多长期跟踪研究来验证这些发现。
""",
    
    "mixed_content": """
项目管理最佳实践指南

## 概述

项目管理是确保项目成功的关键。本指南总结了行业最佳实践。

### 核心原则

项目管理的成功基于以下核心原则：

1. 明确的目标设定
2. 有效的沟通机制
3. 风险管理策略
4. 持续的进度监控

### 实施步骤

#### 第一阶段：项目启动

关键活动：
- 定义项目范围
- 识别利益相关者
- 制定项目章程

重要提示：项目启动阶段的充分准备能够避免后期90%的问题。

#### 第二阶段：规划

详细规划包括：

```
项目计划要素：
├── 时间计划
├── 资源分配
├── 预算制定
└── 质量标准
```

注意事项：规划阶段应该占用项目总时间的20-30%。

#### 第三阶段：执行与监控

执行要点：
• 定期团队会议
• 进度跟踪
• 问题解决
• 变更管理

关键指标监控：
- 进度偏差
- 成本偏差
- 质量指标
- 团队绩效

### 常见陷阱与解决方案

1. **范围蔓延**
   - 问题：项目范围不断扩大
   - 解决：严格的变更控制流程

2. **沟通不畅**
   - 问题：信息传递不及时
   - 解决：建立定期沟通机制

3. **资源冲突**
   - 问题：资源分配不合理
   - 解决：优先级排序和资源平衡

### 总结

成功的项目管理需要：
- 系统的方法论
- 有效的工具支持
- 团队的积极参与
- 持续的改进意识

记住：好的项目管理不仅关注结果，更重视过程的优化。
"""
}


async def test_chunking_strategies():
    """测试不同的分块策略"""
    results = {}
    
    for doc_name, content in TEST_DOCUMENTS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"测试文档: {doc_name}")
        logger.info(f"文档长度: {len(content)} 字符")
        
        doc_results = {}
        
        # 测试不同的分块策略
        strategies = [
            ChunkingStrategy.FIXED_SIZE,
            ChunkingStrategy.SEMANTIC,
            ChunkingStrategy.SENTENCE_BASED,
            ChunkingStrategy.HYBRID
        ]
        
        for strategy in strategies:
            logger.info(f"\n测试策略: {strategy.value}")
            
            try:
                # 执行分块
                chunks = await document_chunker.chunk_document(
                    text=content,
                    document_id=f"test_{doc_name}",
                    strategy=strategy,
                    chunk_size=500,
                    chunk_overlap=100
                )
                
                # 收集统计信息
                stats = analyze_chunks(chunks)
                doc_results[strategy.value] = stats
                
                # 打印统计信息
                print_chunk_stats(stats)
                
                # 如果是混合策略，展示更多细节
                if strategy == ChunkingStrategy.HYBRID:
                    print_hybrid_details(chunks)
                
            except Exception as e:
                logger.error(f"策略 {strategy.value} 失败: {str(e)}")
                doc_results[strategy.value] = {"error": str(e)}
        
        results[doc_name] = doc_results
    
    return results


def analyze_chunks(chunks: List[Any]) -> Dict[str, Any]:
    """分析分块结果"""
    if not chunks:
        return {"error": "No chunks generated"}
    
    # 基础统计
    chunk_sizes = [len(chunk.content) for chunk in chunks]
    
    stats = {
        "chunk_count": len(chunks),
        "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
        "min_chunk_size": min(chunk_sizes),
        "max_chunk_size": max(chunk_sizes),
        "total_size": sum(chunk_sizes),
    }
    
    # 分析块类型分布
    chunk_types = {}
    key_chunks = 0
    
    for chunk in chunks:
        if hasattr(chunk, 'metadata') and isinstance(chunk.metadata, dict):
            chunk_type = chunk.metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            if chunk.metadata.get('is_key_chunk', False):
                key_chunks += 1
    
    stats["chunk_types"] = chunk_types
    stats["key_chunks"] = key_chunks
    
    # 计算覆盖率（检查是否有遗漏）
    if chunks:
        coverage = calculate_coverage(chunks)
        stats["coverage"] = coverage
    
    return stats


def calculate_coverage(chunks: List[Any]) -> Dict[str, Any]:
    """计算文本覆盖率"""
    positions = []
    
    for chunk in chunks:
        if hasattr(chunk, 'start_char') and hasattr(chunk, 'end_char'):
            positions.append((chunk.start_char, chunk.end_char))
    
    if not positions:
        return {"coverage_ratio": 0, "gaps": []}
    
    # 排序并合并重叠区间
    positions.sort()
    merged = [positions[0]]
    
    for start, end in positions[1:]:
        if start <= merged[-1][1]:
            # 重叠，合并
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    
    # 计算覆盖的总长度
    covered_length = sum(end - start for start, end in merged)
    
    # 找出间隙
    gaps = []
    for i in range(len(merged) - 1):
        gap_start = merged[i][1]
        gap_end = merged[i + 1][0]
        if gap_end - gap_start > 10:  # 忽略小间隙
            gaps.append((gap_start, gap_end))
    
    return {
        "covered_ranges": len(merged),
        "covered_length": covered_length,
        "gaps": len(gaps),
        "largest_gap": max(gaps, key=lambda x: x[1] - x[0])[1] - max(gaps, key=lambda x: x[1] - x[0])[0] if gaps else 0
    }


def print_chunk_stats(stats: Dict[str, Any]):
    """打印分块统计信息"""
    if "error" in stats:
        logger.error(f"错误: {stats['error']}")
        return
    
    logger.info(f"  块数量: {stats['chunk_count']}")
    logger.info(f"  平均大小: {stats['avg_chunk_size']:.1f} 字符")
    logger.info(f"  大小范围: {stats['min_chunk_size']} - {stats['max_chunk_size']} 字符")
    
    if "chunk_types" in stats and stats["chunk_types"]:
        logger.info(f"  块类型分布: {stats['chunk_types']}")
    
    if "key_chunks" in stats:
        logger.info(f"  关键块数量: {stats['key_chunks']}")
    
    if "coverage" in stats:
        coverage = stats["coverage"]
        logger.info(f"  覆盖范围数: {coverage.get('covered_ranges', 0)}")
        logger.info(f"  间隙数: {coverage.get('gaps', 0)}")


def print_hybrid_details(chunks: List[Any]):
    """打印混合策略的详细信息"""
    logger.info("\n混合策略详细信息:")
    
    # 统计不同类型的块
    sliding_windows = 0
    context_enhanced = 0
    high_quality = 0
    
    for chunk in chunks:
        if hasattr(chunk, 'metadata') and isinstance(chunk.metadata, dict):
            metadata = chunk.metadata
            
            if metadata.get('chunk_type') == 'sliding_window':
                sliding_windows += 1
            
            if metadata.get('has_context', False):
                context_enhanced += 1
            
            if metadata.get('quality_score', 0) > 0.8:
                high_quality += 1
    
    logger.info(f"  滑动窗口块: {sliding_windows}")
    logger.info(f"  包含上下文: {context_enhanced}")
    logger.info(f"  高质量块: {high_quality}")


async def test_retrieval_optimization():
    """测试检索优化效果"""
    logger.info("\n" + "="*60)
    logger.info("测试检索优化效果")
    
    # 使用一个包含多个相关概念的文档
    test_doc = TEST_DOCUMENTS["technical_doc"]
    
    # 创建混合分块器
    hybrid_chunker = create_hybrid_chunker(
        chunk_size=400,
        chunk_overlap=100,
        enable_context_windows=True,
        enable_sliding_windows=True,
        enable_key_info_extraction=True
    )
    
    # 执行分块
    chunks = await hybrid_chunker.chunk_text(
        test_doc,
        {"document_id": "test_optimization"}
    )
    
    # 模拟检索场景
    test_queries = [
        "深度学习的核心概念",
        "CNN的主要组件",
        "RNN的优势",
        "深度学习的应用领域",
        "未来发展方向"
    ]
    
    logger.info(f"\n生成了 {len(chunks)} 个优化块")
    
    # 分析每个查询可能命中的块
    for query in test_queries:
        logger.info(f"\n查询: '{query}'")
        relevant_chunks = find_relevant_chunks(chunks, query)
        logger.info(f"  可能相关的块: {len(relevant_chunks)}")
        
        if relevant_chunks:
            best_chunk = relevant_chunks[0]
            logger.info(f"  最佳匹配块类型: {best_chunk.metadata.get('chunk_type', 'unknown')}")
            logger.info(f"  包含关键信息: {best_chunk.metadata.get('is_key_chunk', False)}")
            logger.info(f"  质量分数: {best_chunk.metadata.get('quality_score', 0):.2f}")


def find_relevant_chunks(chunks: List[Any], query: str) -> List[Any]:
    """简单的相关性查找（实际应用中应使用向量检索）"""
    relevant = []
    query_lower = query.lower()
    
    for chunk in chunks:
        content_lower = chunk.content.lower()
        
        # 简单的关键词匹配
        if any(keyword in content_lower for keyword in query_lower.split()):
            relevant.append(chunk)
    
    # 按质量分数排序
    relevant.sort(
        key=lambda x: x.metadata.get('quality_score', 0) if hasattr(x, 'metadata') else 0,
        reverse=True
    )
    
    return relevant[:5]  # 返回前5个


async def main():
    """主函数"""
    logger.info("开始测试优化的文档分块策略")
    
    # 1. 测试不同策略的效果
    results = await test_chunking_strategies()
    
    # 2. 测试检索优化
    await test_retrieval_optimization()
    
    # 3. 保存结果
    output_file = Path("test_results/chunking_optimization_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n测试结果已保存到: {output_file}")
    
    # 4. 生成优化建议
    print_optimization_recommendations(results)


def print_optimization_recommendations(results: Dict[str, Any]):
    """打印优化建议"""
    logger.info("\n" + "="*60)
    logger.info("优化建议")
    
    for doc_name, doc_results in results.items():
        logger.info(f"\n文档类型: {doc_name}")
        
        # 找出最佳策略
        best_strategy = None
        best_score = 0
        
        for strategy, stats in doc_results.items():
            if "error" not in stats:
                # 计算综合分数（简化版）
                score = 0
                if stats.get("key_chunks", 0) > 0:
                    score += 30
                if 300 <= stats.get("avg_chunk_size", 0) <= 600:
                    score += 20
                if stats.get("coverage", {}).get("gaps", 1) == 0:
                    score += 20
                if stats.get("chunk_count", 0) > 5:
                    score += 10
                
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
        
        if best_strategy:
            logger.info(f"  推荐策略: {best_strategy}")
            logger.info(f"  原因: 综合评分最高 ({best_score}分)")
        
        # 特定建议
        if "technical" in doc_name:
            logger.info("  建议: 使用混合策略，启用结构识别和关键信息提取")
        elif "research" in doc_name:
            logger.info("  建议: 使用语义分块，保持段落完整性")
        elif "mixed" in doc_name:
            logger.info("  建议: 使用混合策略，适应多样化内容")


if __name__ == "__main__":
    asyncio.run(main())