#!/usr/bin/env python3
"""测试AAG分析规划功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aag.agents.planner import PlannerAgent, AnalysisGoal
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文档 - 学术论文示例
ACADEMIC_PAPER = """
# Deep Learning for Natural Language Processing: A Comprehensive Survey

## Abstract

This paper presents a comprehensive survey of deep learning techniques in natural language processing (NLP). We review the evolution from traditional methods to modern transformer-based architectures, analyze current state-of-the-art models, and discuss future research directions. Our analysis covers 150+ papers published between 2018-2024.

## 1. Introduction

Natural Language Processing has undergone a paradigm shift with the advent of deep learning. The introduction of transformers in 2017 marked a turning point, leading to unprecedented improvements in various NLP tasks.

### 1.1 Motivation

The exponential growth in textual data and the limitations of traditional NLP methods necessitate more sophisticated approaches. Deep learning offers:
- Automatic feature extraction
- End-to-end learning
- Transfer learning capabilities
- Scalability to large datasets

### 1.2 Contributions

This survey makes the following contributions:
1. Comprehensive taxonomy of deep learning methods in NLP
2. Comparative analysis of architectures
3. Performance benchmarks across tasks
4. Future research directions

## 2. Background and Related Work

### 2.1 Traditional NLP Methods

Before deep learning, NLP relied on:
- Rule-based systems
- Statistical methods (HMM, CRF)
- Feature engineering
- Bag-of-words representations

### 2.2 Early Neural Approaches

- Word2Vec (2013): Distributed word representations
- GloVe (2014): Global vectors for word representation
- LSTM/GRU (2014-2015): Sequential modeling

## 3. Deep Learning Architectures

### 3.1 Convolutional Neural Networks
CNNs in NLP capture local patterns and n-gram features.

### 3.2 Recurrent Neural Networks
RNNs model sequential dependencies but suffer from vanishing gradients.

### 3.3 Transformer Architecture
Self-attention mechanism enables parallel processing and long-range dependencies.

## 4. State-of-the-Art Models

### 4.1 BERT and Variants
- BERT: Bidirectional pre-training
- RoBERTa: Robustly optimized BERT
- ALBERT: Parameter-efficient variant

### 4.2 GPT Family
- GPT-2: Unsupervised language generation
- GPT-3: Few-shot learning capabilities
- GPT-4: Multi-modal understanding

## 5. Applications and Results

[Detailed experimental results and benchmarks]

## 6. Challenges and Future Directions

- Computational efficiency
- Interpretability
- Multimodal integration
- Low-resource languages

## 7. Conclusion

Deep learning has revolutionized NLP, but significant challenges remain.

## References
[150+ academic references]
"""

# 商业文档示例
BUSINESS_DOCUMENT = """
# Q4 2024 营销策略方案

## 执行摘要

本方案旨在通过数字化转型和精准营销，在Q4实现销售额增长35%的目标。

## 市场分析

当前市场呈现以下特征：
- 消费者行为数字化
- 竞争对手加大投入
- 新兴渠道崛起

## 策略目标

1. 品牌知名度提升50%
2. 获客成本降低20%
3. 客户留存率达到85%

## 实施计划

### 第一阶段（10月）
- 启动社交媒体营销
- 优化SEO/SEM策略

### 第二阶段（11月）
- 推出会员体系
- 开展促销活动

### 第三阶段（12月）
- 年终大促
- 客户关怀计划

## 预算分配

总预算：500万元
- 数字营销：60%
- 传统媒体：20%
- 活动执行：20%
"""


async def test_academic_paper_planning():
    """测试学术论文的分析规划"""
    logger.info("=== 测试学术论文分析规划 ===")
    
    planner = PlannerAgent()
    
    # 深度理解目标
    result = await planner.process({
        "document_content": ACADEMIC_PAPER,
        "document_id": "nlp_survey_001",
        "analysis_goal": AnalysisGoal.DEEP_UNDERSTANDING.value,
        "time_budget": 600,  # 10分钟
        "cost_budget": 1.5   # $1.5
    })
    
    if result["success"]:
        logger.info("分析规划成功")
        plan = result["result"]
        
        # 显示文档评估
        assessment = plan["document_assessment"]
        logger.info(f"\n文档评估:")
        logger.info(f"  类别: {assessment['category']}")
        logger.info(f"  复杂度: {assessment['complexity']}")
        logger.info(f"  质量: {assessment['quality']}")
        
        # 显示推荐分析
        logger.info(f"\n推荐的分析 ({len(plan['recommended_analyses'])}个):")
        for analysis in plan["recommended_analyses"]:
            logger.info(f"  - {analysis['analysis_type']} ({analysis['priority']}优先级)")
            logger.info(f"    时间: {analysis['estimated_time']}秒, 成本: ${analysis['estimated_cost']}")
        
        # 显示执行计划
        execution = plan["execution_plan"]
        logger.info(f"\n执行计划:")
        logger.info(f"  总时间: {execution['total_time']}秒")
        logger.info(f"  总成本: ${execution['total_cost']}")
        logger.info(f"  阶段数: {len(execution['phases'])}")
    else:
        logger.error(f"规划失败: {result.get('error')}")


async def test_business_document_planning():
    """测试商业文档的分析规划"""
    logger.info("\n\n=== 测试商业文档分析规划 ===")
    
    planner = PlannerAgent()
    
    # 快速概览目标，预算有限
    result = await planner.process({
        "document_content": BUSINESS_DOCUMENT,
        "document_id": "marketing_plan_001",
        "analysis_goal": AnalysisGoal.QUICK_OVERVIEW.value,
        "time_budget": 120,  # 2分钟
        "cost_budget": 0.2,  # $0.2
        "user_requirements": "重点关注预算分配和ROI预期"
    })
    
    if result["success"]:
        logger.info("分析规划成功")
        plan = result["result"]
        
        # 显示针对性分析
        logger.info(f"\n文档类别: {plan['document_assessment']['category']}")
        logger.info(f"推荐分析数: {len(plan['recommended_analyses'])}")
        
        # 显示警告和建议
        if plan.get("warnings"):
            logger.info("\n警告:")
            for warning in plan["warnings"]:
                logger.info(f"  ⚠️  {warning}")
        
        if plan.get("recommendations"):
            logger.info("\n建议:")
            for rec in plan["recommendations"]:
                logger.info(f"  💡 {rec}")
    else:
        logger.error(f"规划失败: {result.get('error')}")


async def test_custom_requirements():
    """测试自定义需求的分析规划"""
    logger.info("\n\n=== 测试自定义需求分析规划 ===")
    
    planner = PlannerAgent()
    
    # 自定义分析目标
    result = await planner.process({
        "document_content": ACADEMIC_PAPER,
        "document_id": "custom_analysis_001",
        "analysis_goal": AnalysisGoal.CUSTOM.value,
        "user_requirements": """
        我需要：
        1. 提取所有提到的深度学习模型
        2. 分析各模型的优缺点对比
        3. 找出未来研究方向的具体建议
        4. 生成一份可以用于演讲的大纲
        """,
        "time_budget": 300,
        "cost_budget": 0.8
    })
    
    if result["success"]:
        logger.info("自定义规划成功")
        plan = result["result"]
        
        # 显示如何满足自定义需求
        logger.info(f"\n为满足自定义需求，推荐以下分析:")
        for i, analysis in enumerate(plan["recommended_analyses"], 1):
            logger.info(f"{i}. {analysis['analysis_type']}")
            logger.info(f"   预期价值: {analysis['expected_value']}")
    else:
        logger.error(f"规划失败: {result.get('error')}")


async def test_progress_evaluation():
    """测试进度评估功能"""
    logger.info("\n\n=== 测试进度评估功能 ===")
    
    planner = PlannerAgent()
    
    # 先创建一个计划
    plan_result = await planner.process({
        "document_content": ACADEMIC_PAPER,
        "document_id": "progress_test_001",
        "analysis_goal": AnalysisGoal.DEEP_UNDERSTANDING.value,
        "time_budget": 300,
        "cost_budget": 1.0
    })
    
    if not plan_result["success"]:
        logger.error("创建计划失败")
        return
    
    plan = plan_result["result"]
    
    # 模拟已完成一些分析
    completed_analyses = ["skim", "summary_level_2", "outline_logical"]
    
    # 评估进度
    progress_result = await planner.evaluate_progress(
        document_id="progress_test_001",
        plan=plan,
        completed_analyses=completed_analyses
    )
    
    if progress_result["success"]:
        logger.info("进度评估成功")
        progress = progress_result["result"]
        
        logger.info(f"\n进度报告:")
        logger.info(f"  完成率: {progress['completion_rate']*100:.1f}%")
        logger.info(f"  状态: {progress['status']}")
        logger.info(f"  已完成: {len(progress['completed_analyses'])}个分析")
        logger.info(f"  待完成: {len(progress['pending_analyses'])}个分析")
        logger.info(f"  剩余时间: {progress['remaining_time']}秒")
        logger.info(f"  剩余成本: ${progress['remaining_cost']}")
        
        if progress["recommendations"]:
            logger.info("\n进度建议:")
            for rec in progress["recommendations"]:
                logger.info(f"  - {rec}")
    else:
        logger.error(f"进度评估失败: {progress_result.get('error')}")


async def test_budget_adjustment():
    """测试预算调整功能"""
    logger.info("\n\n=== 测试预算调整功能 ===")
    
    planner = PlannerAgent()
    
    # 创建一个超预算的需求
    result = await planner.process({
        "document_content": ACADEMIC_PAPER,
        "document_id": "budget_test_001",
        "analysis_goal": AnalysisGoal.DEEP_UNDERSTANDING.value,
        "time_budget": 60,    # 只有1分钟
        "cost_budget": 0.1    # 只有$0.1
    })
    
    if result["success"]:
        logger.info("预算调整规划成功")
        plan = result["result"]
        
        logger.info(f"\n调整后的计划:")
        logger.info(f"  分析数量: {len(plan['recommended_analyses'])}")
        logger.info(f"  总时间: {plan['execution_plan']['total_time']}秒 (预算: 60秒)")
        logger.info(f"  总成本: ${plan['execution_plan']['total_cost']} (预算: $0.1)")
        
        # 显示警告信息
        if plan.get("warnings"):
            logger.info("\n预算警告:")
            for warning in plan["warnings"]:
                logger.info(f"  ⚠️  {warning}")
    else:
        logger.error(f"规划失败: {result.get('error')}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_academic_paper_planning())
    asyncio.run(test_business_document_planning())
    asyncio.run(test_custom_requirements())
    asyncio.run(test_progress_evaluation())
    asyncio.run(test_budget_adjustment())
    
    logger.info("\n\n=== 所有规划测试完成 ===")