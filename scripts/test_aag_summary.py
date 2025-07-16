#!/usr/bin/env python3
"""测试AAG渐进式摘要功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aag.agents import ProgressiveSummaryAgent, SummaryLevel
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文档内容 - 一篇关于量子计算的科普文章
TEST_DOCUMENT = """
# 量子计算：未来的计算革命

## 引言

量子计算是基于量子力学原理的全新计算范式，它有望在特定问题上实现指数级的计算加速。不同于传统计算机使用的二进制位（0或1），量子计算机使用量子位（qubit），可以同时处于0和1的叠加态。这种特性使得量子计算机在处理某些复杂问题时具有巨大优势。

## 量子计算的基本原理

### 1. 量子叠加

量子叠加是量子力学的核心概念之一。在量子世界中，一个粒子可以同时处于多个状态的叠加。对于量子位来说，它可以同时是0和1，直到被测量时才会"坍缩"到确定的状态。这种特性使得n个量子位可以同时表示2^n个状态，大大增加了信息处理能力。

### 2. 量子纠缠

量子纠缠是指两个或多个量子粒子之间存在的特殊关联。当粒子处于纠缠态时，对其中一个粒子的测量会瞬间影响另一个粒子的状态，无论它们相距多远。这种"幽灵般的超距作用"是量子计算实现并行处理的关键。

### 3. 量子干涉

量子干涉允许量子算法增强正确答案的概率振幅，同时抑制错误答案的概率振幅。通过巧妙设计的量子算法，可以利用干涉效应使得测量时获得正确答案的概率接近1。

## 量子计算的技术实现

### 1. 物理实现方式

目前主要的量子计算实现方式包括：

- **超导量子比特**：使用超导约瑟夫森结，在极低温下工作（接近绝对零度）
- **离子阱**：使用被电磁场囚禁的离子作为量子位
- **拓扑量子比特**：利用任意子的拓扑性质，理论上更稳定
- **光量子计算**：使用光子作为信息载体

### 2. 主要挑战

量子计算面临的主要技术挑战包括：

- **量子退相干**：量子态很容易受到环境干扰而失去相干性
- **错误率高**：当前量子操作的错误率远高于经典计算
- **可扩展性**：增加量子位数量的同时保持系统稳定性困难
- **量子纠错**：需要大量物理量子位来实现一个逻辑量子位

## 量子算法与应用

### 1. 著名的量子算法

- **Shor算法**：用于大数分解，威胁现有的RSA加密体系
- **Grover算法**：提供平方根级别的搜索加速
- **量子模拟**：模拟复杂的量子系统，如分子和材料
- **QAOA**：量子近似优化算法，用于组合优化问题

### 2. 潜在应用领域

- **密码学**：破解现有加密，开发量子安全加密
- **药物研发**：模拟分子相互作用，加速新药发现
- **材料科学**：设计新型材料和催化剂
- **金融建模**：优化投资组合，风险分析
- **人工智能**：加速机器学习算法

## 产业现状与发展

### 1. 主要参与者

- **科技巨头**：Google、IBM、Microsoft、Amazon等
- **初创公司**：IonQ、Rigetti、PsiQuantum等
- **研究机构**：MIT、Oxford、中科院等
- **国家项目**：美国、中国、欧盟的量子计划

### 2. 里程碑事件

- 2019年：Google宣布实现"量子优越性"
- 2021年：中国"九章"光量子计算机创造新纪录
- 2023年：IBM发布1000+量子位路线图

## 未来展望

### 1. 近期目标（5-10年）

- 实现含噪声中等规模量子（NISQ）设备的实际应用
- 开发更多量子算法和应用
- 提高量子位质量和数量

### 2. 长期愿景（10-20年）

- 实现容错量子计算
- 量子计算机成为主流计算资源
- 量子互联网的建立

## 结论

量子计算代表着计算技术的范式转变。虽然目前仍面临诸多技术挑战，但其潜在的变革性影响使得全球都在加大投入。随着技术的不断进步，量子计算有望在未来几十年内彻底改变我们解决复杂问题的方式，开启计算的新纪元。

对于企业和研究机构来说，现在是开始了解和准备量子计算时代的关键时期。虽然通用量子计算机可能还需要多年才能实现，但在特定领域的量子优势已经开始显现。我们正站在一个新时代的门槛上，量子计算将重新定义什么是可计算的。
"""


async def test_single_summary():
    """测试单个级别的摘要"""
    logger.info("开始测试单个级别的摘要生成...")
    
    summarizer = ProgressiveSummaryAgent()
    
    # 测试Level 2摘要（200字）
    result = await summarizer.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "quantum_computing_001",
        "summary_level": SummaryLevel.LEVEL_2.value
    })
    
    if result["success"]:
        logger.info("Level 2摘要生成成功！")
        logger.info(f"执行时间: {result['metadata']['duration']:.2f}秒")
        logger.info(f"Token使用量: {result['metadata']['tokens_used']}")
        
        summary_result = result["result"]
        logger.info("\n=== 200字摘要 ===")
        logger.info(summary_result["summary"])
        logger.info(f"\n字数: {summary_result['word_count']}")
        logger.info(f"关键点数量: {len(summary_result.get('key_points', []))}")
    else:
        logger.error(f"摘要生成失败: {result.get('error')}")


async def test_progressive_summaries():
    """测试渐进式摘要（多个级别）"""
    logger.info("\n\n=== 测试渐进式摘要生成 ===")
    
    summarizer = ProgressiveSummaryAgent()
    previous_summaries = {}
    
    # 依次生成Level 1到Level 3的摘要
    for level in [SummaryLevel.LEVEL_1, SummaryLevel.LEVEL_2, SummaryLevel.LEVEL_3]:
        logger.info(f"\n生成 {level.value} 摘要...")
        
        result = await summarizer.process({
            "document_content": TEST_DOCUMENT,
            "document_id": "quantum_computing_001",
            "summary_level": level.value,
            "previous_summaries": previous_summaries
        })
        
        if result["success"]:
            summary_result = result["result"]
            logger.info(f"✓ {level.value} 生成成功")
            logger.info(f"字数: {summary_result['word_count']}")
            logger.info(f"摘要内容:\n{summary_result['summary'][:200]}...")  # 只显示前200字
            
            # 保存摘要供下一级别使用
            previous_summaries[level.value] = summary_result["summary"]
        else:
            logger.error(f"✗ {level.value} 生成失败: {result.get('error')}")
            break


async def test_all_levels():
    """测试生成所有级别的摘要"""
    logger.info("\n\n=== 测试一次性生成所有级别摘要 ===")
    
    summarizer = ProgressiveSummaryAgent()
    all_summaries = await summarizer.generate_all_levels(
        document_content=TEST_DOCUMENT,
        document_id="quantum_computing_001"
    )
    
    logger.info(f"成功生成 {len(all_summaries)} 个级别的摘要")
    
    for level, summary_result in all_summaries.items():
        logger.info(f"\n{level}:")
        logger.info(f"  字数: {summary_result['word_count']}")
        logger.info(f"  关键点: {len(summary_result.get('key_points', []))}")
        if level in [SummaryLevel.LEVEL_4.value, SummaryLevel.LEVEL_5.value]:
            logger.info(f"  章节数: {len(summary_result.get('sections', []))}")
            logger.info(f"  建议数: {len(summary_result.get('recommendations', []))}")


async def test_cache():
    """测试缓存功能"""
    logger.info("\n\n=== 测试缓存功能 ===")
    
    summarizer = ProgressiveSummaryAgent()
    
    # 第一次生成
    logger.info("第一次生成摘要...")
    result1 = await summarizer.process({
        "document_content": TEST_DOCUMENT[:1000],  # 使用较短的文档测试
        "document_id": "cache_test_001",
        "summary_level": SummaryLevel.LEVEL_1.value
    })
    
    # 第二次生成（应该从缓存读取）
    logger.info("第二次生成摘要（应该使用缓存）...")
    result2 = await summarizer.process({
        "document_content": TEST_DOCUMENT[:1000],
        "document_id": "cache_test_001",
        "summary_level": SummaryLevel.LEVEL_1.value
    })
    
    if result2["metadata"].get("from_cache"):
        logger.info("✓ 成功从缓存读取摘要")
        logger.info(f"  第一次耗时: {result1['metadata']['duration']:.2f}秒")
        logger.info(f"  第二次耗时: {result2['metadata']['duration']:.2f}秒")
    else:
        logger.warning("✗ 未能从缓存读取摘要")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_single_summary())
    asyncio.run(test_progressive_summaries())
    asyncio.run(test_all_levels())
    asyncio.run(test_cache())