#!/usr/bin/env python3
"""测试AAG快速略读功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aag.agents import SkimmerAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文档内容
TEST_DOCUMENT = """
# 深度学习在自然语言处理中的应用研究

## 摘要

本文综述了深度学习技术在自然语言处理（NLP）领域的最新进展和应用。我们系统地回顾了从早期的词向量表示到现代的Transformer架构的演进历程，重点分析了BERT、GPT等预训练语言模型的技术原理和实际应用效果。研究表明，深度学习已经在机器翻译、文本分类、情感分析、问答系统等多个NLP任务上取得了突破性进展。

## 1. 引言

自然语言处理是人工智能领域的重要分支，旨在让计算机理解、解释和生成人类语言。近年来，深度学习技术的快速发展为NLP带来了革命性的变化。传统的基于规则和统计的方法逐渐被深度神经网络所取代，在各种NLP任务上都取得了前所未有的性能提升。

## 2. 深度学习基础

### 2.1 神经网络架构

深度学习的核心是多层神经网络，通过非线性变换学习数据的层次化表示。在NLP中，常用的架构包括：

- 循环神经网络（RNN）：适合处理序列数据
- 长短期记忆网络（LSTM）：解决RNN的梯度消失问题
- 门控循环单元（GRU）：LSTM的简化版本
- Transformer：基于自注意力机制的架构

### 2.2 词向量表示

词向量是深度学习在NLP中的基础，主要方法包括：

- Word2Vec：包括CBOW和Skip-gram两种模型
- GloVe：结合全局统计信息的词向量方法
- FastText：考虑子词信息的词向量表示

## 3. 预训练语言模型

### 3.1 BERT（Bidirectional Encoder Representations from Transformers）

BERT通过掩码语言模型（MLM）和下一句预测（NSP）任务进行预训练，能够捕获双向的上下文信息。其主要特点：

- 双向编码：同时考虑左右上下文
- 多任务预训练：MLM和NSP联合训练
- 微调范式：预训练+任务特定微调

### 3.2 GPT系列

GPT采用自回归语言模型进行预训练，从GPT-1到GPT-4，模型规模和性能不断提升：

- GPT-1：展示了预训练的有效性
- GPT-2：大规模无监督预训练
- GPT-3：少样本学习能力
- GPT-4：多模态理解能力

## 4. 应用场景

### 4.1 机器翻译

神经机器翻译（NMT）已成为主流，基于Transformer的模型在多种语言对上达到人类水平。

### 4.2 文本分类

深度学习模型在新闻分类、垃圾邮件检测、情感分析等任务上表现优异。

### 4.3 问答系统

基于BERT的模型在阅读理解和开放域问答任务上取得突破。

### 4.4 文本生成

GPT系列模型展示了强大的文本生成能力，应用于对话系统、文章创作等。

## 5. 挑战与展望

尽管深度学习在NLP领域取得了巨大成功，但仍面临一些挑战：

- 计算资源需求：大模型训练成本高昂
- 可解释性：深度模型的决策过程难以解释
- 数据偏见：模型可能学习到训练数据中的偏见
- 领域适应：跨领域泛化能力有限

未来的研究方向包括：

- 更高效的模型架构
- 多模态融合
- 持续学习能力
- 可解释AI

## 6. 结论

深度学习已经成为NLP领域的主导技术，在多个任务上实现了性能突破。随着技术的不断进步，我们期待看到更多创新应用，同时也需要关注伦理、隐私和社会影响等问题。
"""


async def test_skim_agent():
    """测试略读Agent"""
    logger.info("开始测试AAG快速略读功能...")
    
    # 创建SkimmerAgent
    skimmer = SkimmerAgent()
    
    # 执行略读
    result = await skimmer.process({
        "document_content": TEST_DOCUMENT,
        "document_type": "学术论文"
    })
    
    if result["success"]:
        logger.info("略读成功！")
        logger.info(f"执行时间: {result['metadata']['duration']:.2f}秒")
        logger.info(f"Token使用量: {result['metadata']['tokens_used']}")
        
        skim_result = result["result"]
        logger.info("\n=== 略读结果 ===")
        logger.info(f"文档类型: {skim_result.get('document_type')}")
        logger.info(f"核心主题: {skim_result.get('core_topic')}")
        
        logger.info("\n关键要点:")
        for i, point in enumerate(skim_result.get('key_points', []), 1):
            logger.info(f"  {i}. {point}")
        
        target_audience = skim_result.get('target_audience', [])
        if isinstance(target_audience, str):
            logger.info(f"\n目标受众: {target_audience}")
        else:
            logger.info(f"\n目标受众: {', '.join(target_audience)}")
        
        quality = skim_result.get('quality_assessment', {})
        logger.info(f"\n质量评估: {quality.get('level')} - {quality.get('reason')}")
        
        logger.info("\n建议的分析方向:")
        for i, suggestion in enumerate(skim_result.get('analysis_suggestions', []), 1):
            logger.info(f"  {i}. {suggestion}")
    else:
        logger.error(f"略读失败: {result.get('error')}")


async def test_with_short_document():
    """测试短文档"""
    short_doc = """
    这是一个测试文档。
    它包含了一些基本信息。
    用于测试AAG系统的快速略读功能。
    """
    
    logger.info("\n\n=== 测试短文档 ===")
    
    skimmer = SkimmerAgent()
    result = await skimmer.process({
        "document_content": short_doc,
        "document_type": "测试文档"
    })
    
    if result["success"]:
        logger.info("短文档略读成功！")
        logger.info(f"核心主题: {result['result'].get('core_topic')}")
    else:
        logger.error(f"短文档略读失败: {result.get('error')}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_skim_agent())
    asyncio.run(test_with_short_document())