#!/usr/bin/env python3
"""测试AAG深度分析功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aag.agents.analyzer import (
    EvidenceChainAnalyzer, 
    CrossReferenceAnalyzer,
    CriticalThinkingAnalyzer,
    DeepAnalyzer
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文档 - 一篇关于AI伦理的论文
TEST_DOCUMENT = """
# 人工智能伦理：挑战与机遇

## 摘要

人工智能（AI）的快速发展带来了前所未有的机遇，同时也引发了深刻的伦理挑战。本文探讨了AI伦理的核心问题，包括算法偏见、隐私保护、透明度和问责制。通过分析具体案例和现有框架，我们提出了一个综合性的AI伦理治理模型。

## 1. 引言

随着AI技术在医疗、金融、司法等关键领域的广泛应用，确保AI系统的伦理性变得至关重要。根据MIT的研究（2023），超过70%的企业在部署AI时面临伦理困境。

## 2. 算法偏见问题

### 2.1 偏见的来源

算法偏见主要源于三个方面：
1. **训练数据偏见**：历史数据中固有的社会偏见被算法学习和放大
2. **设计者偏见**：开发团队的认知局限影响算法设计
3. **反馈循环**：系统输出强化现有偏见，形成恶性循环

### 2.2 案例分析

2019年，某招聘AI系统被发现对女性候选人存在系统性歧视。调查显示，该系统基于过去10年的招聘数据训练，而这些数据反映了技术行业的性别失衡。

## 3. 隐私与数据保护

### 3.1 数据收集的伦理边界

AI系统需要大量数据进行训练，但数据收集必须遵循以下原则：
- **知情同意**：用户应充分了解数据用途
- **目的限制**：数据仅用于声明的目的
- **最小化原则**：仅收集必要的数据

### 3.2 技术解决方案

联邦学习和差分隐私等技术为保护隐私提供了新途径。Google的研究表明，联邦学习可以在不传输原始数据的情况下训练高质量模型。

## 4. 透明度与可解释性

### 4.1 黑箱问题

深度学习模型的复杂性导致决策过程难以理解。在医疗诊断等高风险领域，这种不透明性是不可接受的。

### 4.2 可解释AI的进展

LIME、SHAP等方法提供了模型解释的工具，但仍存在局限性。欧盟的AI法案要求高风险AI系统必须提供人类可理解的解释。

## 5. 问责制框架

### 5.1 责任分配

当AI系统造成损害时，责任应如何分配？这涉及开发者、部署者和使用者等多方。

### 5.2 监管建议

我们提出以下监管框架：
1. 建立AI审计机制
2. 强制风险评估
3. 设立独立监督委员会
4. 实施分级管理

## 6. 综合治理模型

基于以上分析，我们提出FAIR（公平、问责、包容、稳健）治理模型：

- **公平（Fairness）**：消除算法偏见，确保公平对待所有群体
- **问责（Accountability）**：明确责任链，建立追责机制
- **包容（Inclusiveness）**：多方参与决策，考虑不同利益相关者
- **稳健（Robustness）**：确保系统安全可靠，能够应对异常情况

## 7. 结论

AI伦理不是技术问题，而是社会问题。需要技术专家、伦理学者、政策制定者和公众的共同努力。只有建立完善的伦理框架，AI才能真正造福人类。

## 参考文献

1. Smith, J. (2023). "Algorithmic Bias in Machine Learning Systems." MIT Press.
2. European Commission (2024). "AI Act: Regulatory Framework for Artificial Intelligence."
3. Zhang, L. et al. (2023). "Privacy-Preserving Machine Learning: A Survey." Nature Machine Intelligence.
"""


async def test_evidence_chain_analysis():
    """测试证据链分析"""
    logger.info("=== 测试证据链分析 ===")
    
    analyzer = EvidenceChainAnalyzer()
    
    # 聚焦分析特定声明
    focus_claims = [
        "超过70%的企业在部署AI时面临伦理困境",
        "联邦学习可以在不传输原始数据的情况下训练高质量模型"
    ]
    
    result = await analyzer.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "ai_ethics_001",
        "focus_claims": focus_claims
    })
    
    if result["success"]:
        logger.info("证据链分析成功完成")
        logger.info(f"分析耗时: {result['metadata']['duration']:.2f}秒")
        
        analysis = result["result"]
        
        # 显示声明分析
        if "claims" in analysis:
            logger.info(f"\n识别的声明数量: {len(analysis['claims'])}")
            for i, claim in enumerate(analysis['claims'][:3], 1):
                logger.info(f"\n声明 {i}:")
                logger.info(f"  内容: {claim.get('claim', 'N/A')}")
                logger.info(f"  重要性: {claim.get('importance', 'N/A')}")
                logger.info(f"  证据质量: {claim.get('evidence_quality', 'N/A')}")
        
        # 显示整体评估
        if "overall_assessment" in analysis:
            assessment = analysis["overall_assessment"]
            logger.info(f"\n整体评估:")
            logger.info(f"  证据完整性: {assessment.get('evidence_completeness', 'N/A')}/10")
            logger.info(f"  逻辑连贯性: {assessment.get('logical_coherence', 'N/A')}/10")
            logger.info(f"  可信度: {assessment.get('credibility', 'N/A')}/10")
    else:
        logger.error(f"证据链分析失败: {result.get('error')}")


async def test_cross_reference_analysis():
    """测试交叉引用分析"""
    logger.info("\n\n=== 测试交叉引用分析 ===")
    
    analyzer = CrossReferenceAnalyzer()
    
    result = await analyzer.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "ai_ethics_002"
    })
    
    if result["success"]:
        logger.info("交叉引用分析成功完成")
        logger.info(f"分析耗时: {result['metadata']['duration']:.2f}秒")
        
        analysis = result["result"]
        
        # 显示内部引用
        if "internal_references" in analysis:
            logger.info(f"\n内部引用数量: {len(analysis['internal_references'])}")
        
        # 显示概念引用
        if "concept_references" in analysis:
            logger.info(f"\n追踪的概念数量: {len(analysis['concept_references'])}")
            for concept in analysis['concept_references'][:3]:
                logger.info(f"  - {concept.get('concept', 'N/A')}")
        
        # 显示一致性分析
        if "consistency_analysis" in analysis:
            consistency = analysis["consistency_analysis"]
            logger.info(f"\n一致性评分:")
            logger.info(f"  术语一致性: {consistency.get('terminology_consistency', 'N/A')}/10")
            logger.info(f"  逻辑一致性: {consistency.get('logical_consistency', 'N/A')}/10")
            logger.info(f"  数据一致性: {consistency.get('data_consistency', 'N/A')}/10")
    else:
        logger.error(f"交叉引用分析失败: {result.get('error')}")


async def test_critical_thinking_analysis():
    """测试批判性思维分析"""
    logger.info("\n\n=== 测试批判性思维分析 ===")
    
    analyzer = CriticalThinkingAnalyzer()
    
    result = await analyzer.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "ai_ethics_003",
        "analysis_depth": "deep"
    })
    
    if result["success"]:
        logger.info("批判性思维分析成功完成")
        logger.info(f"分析耗时: {result['metadata']['duration']:.2f}秒")
        
        analysis = result["result"]
        
        # 显示论证分析
        if "arguments" in analysis:
            logger.info(f"\n识别的论点数量: {len(analysis['arguments'])}")
            for i, arg in enumerate(analysis['arguments'][:2], 1):
                logger.info(f"\n论点 {i}:")
                logger.info(f"  内容: {arg.get('argument', 'N/A')}")
                logger.info(f"  类型: {arg.get('type', 'N/A')}")
                logger.info(f"  强度: {arg.get('strength', 'N/A')}")
        
        # 显示假设分析
        if "assumptions" in analysis:
            logger.info(f"\n识别的假设数量: {len(analysis['assumptions'])}")
        
        # 显示偏见分析
        if "biases" in analysis:
            logger.info(f"\n识别的偏见数量: {len(analysis['biases'])}")
        
        # 显示批判性评估
        if "critical_assessment" in analysis:
            assessment = analysis["critical_assessment"]
            logger.info(f"\n批判性评估:")
            logger.info(f"  逻辑严密性: {assessment.get('logical_rigor', 'N/A')}/10")
            logger.info(f"  证据质量: {assessment.get('evidence_quality', 'N/A')}/10")
            logger.info(f"  客观性: {assessment.get('objectivity', 'N/A')}/10")
            logger.info(f"  完整性: {assessment.get('completeness', 'N/A')}/10")
    else:
        logger.error(f"批判性思维分析失败: {result.get('error')}")


async def test_deep_analyzer():
    """测试综合深度分析器"""
    logger.info("\n\n=== 测试综合深度分析器 ===")
    
    analyzer = DeepAnalyzer()
    
    # 执行所有类型的分析
    result = await analyzer.analyze(
        document_content=TEST_DOCUMENT,
        document_id="ai_ethics_004",
        analysis_types=None,  # None表示执行所有分析
        focus_claims=["AI系统需要大量数据进行训练"],
        analysis_depth="comprehensive"
    )
    
    if result["success"]:
        logger.info("综合深度分析成功完成")
        logger.info(f"总耗时: {result['metadata']['total_duration']:.2f}秒")
        logger.info(f"总Token使用: {result['metadata']['total_tokens']}")
        logger.info(f"完成的分析数量: {result['metadata']['analysis_count']}")
        
        # 显示各分析结果摘要
        for analysis_type, analysis_result in result["analyses"].items():
            logger.info(f"\n{analysis_type}分析: {'成功' if 'error' not in analysis_result else '失败'}")
    else:
        logger.error("综合深度分析失败")


async def test_cache_behavior():
    """测试缓存行为"""
    logger.info("\n\n=== 测试缓存行为 ===")
    
    analyzer = EvidenceChainAnalyzer()
    
    doc_id = "cache_test_deep"
    doc_content = "这是一个简单的测试文档。它包含一个声明：AI可以提高效率50%。"
    
    # 第一次分析
    logger.info("第一次分析（无缓存）...")
    result1 = await analyzer.process({
        "document_content": doc_content,
        "document_id": doc_id
    })
    
    if result1["success"]:
        duration1 = result1["metadata"]["duration"]
        logger.info(f"第一次分析耗时: {duration1:.2f}秒")
    
    # 第二次分析（应该使用缓存）
    logger.info("\n第二次分析（应该使用缓存）...")
    result2 = await analyzer.process({
        "document_content": doc_content,
        "document_id": doc_id
    })
    
    if result2["success"]:
        duration2 = result2["metadata"]["duration"]
        from_cache = result2["metadata"].get("from_cache", False)
        logger.info(f"第二次分析耗时: {duration2:.2f}秒")
        logger.info(f"是否使用缓存: {from_cache}")
        
        if from_cache and duration1 > 0:
            logger.info(f"速度提升: {duration1/max(duration2, 0.001):.1f}倍")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_evidence_chain_analysis())
    asyncio.run(test_cross_reference_analysis())
    asyncio.run(test_critical_thinking_analysis())
    asyncio.run(test_deep_analyzer())
    asyncio.run(test_cache_behavior())
    
    logger.info("\n\n=== 所有深度分析测试完成 ===")