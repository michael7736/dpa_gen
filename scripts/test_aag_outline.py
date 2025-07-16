#!/usr/bin/env python3
"""测试AAG多维大纲提取功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aag.agents import OutlineAgent, OutlineDimension
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文档内容 - 一篇关于项目管理的文章
TEST_DOCUMENT = """
# 敏捷项目管理：从理论到实践

## 第一章：引言

敏捷项目管理起源于2001年的《敏捷宣言》，由17位软件开发专家共同制定。这种方法论强调个体和互动高于流程和工具，可工作的软件高于详尽的文档，客户合作高于合同谈判，响应变化高于遵循计划。

在过去的20年中，敏捷方法从软件开发领域逐步扩展到其他行业，成为现代项目管理的主流方法之一。

## 第二章：敏捷的核心概念

### 2.1 迭代开发

敏捷项目采用迭代方式进行，每个迭代（Sprint）通常持续2-4周。在每个迭代中，团队完成一个可交付的产品增量。这种方式的好处是：

1. 快速获得反馈
2. 降低项目风险
3. 提高团队士气
4. 增强适应性

### 2.2 自组织团队

敏捷强调团队的自主性和责任感。团队成员共同决定如何完成工作，而不是由管理层下达详细指令。这需要：

- 高度的信任文化
- 清晰的目标定义
- 充分的授权机制
- 持续的沟通协作

### 2.3 持续改进

通过回顾会议（Retrospective），团队定期反思工作流程，识别问题并制定改进措施。

## 第三章：敏捷实施的时间线

### 阶段一：准备期（第1-2周）

- 组建敏捷团队
- 制定项目愿景
- 确定初始产品待办列表
- 搭建开发环境

### 阶段二：试点期（第3-8周）

- 执行第一个Sprint
- 建立日常站会机制
- 完成首个产品增量
- 收集初步反馈

### 阶段三：优化期（第9-16周）

- 调整团队流程
- 优化工具使用
- 扩大敏捷实践范围
- 建立度量体系

### 阶段四：成熟期（第17周后）

- 形成稳定的工作节奏
- 持续交付价值
- 扩展到其他团队
- 建立敏捷文化

## 第四章：因果关系分析

### 4.1 成功因素

**高层支持** → **资源保障** → **团队稳定** → **项目成功**

当管理层真正理解并支持敏捷转型时，会提供必要的资源和政策支持。这种支持确保团队的稳定性，避免频繁的人员变动。稳定的团队能够建立默契，提高协作效率，最终导致项目成功。

### 4.2 失败原因

**形式主义** → **团队抵触** → **执行不力** → **项目失败**

如果只是机械地执行敏捷仪式而不理解其精神，团队成员会感到这是额外的负担。这种抵触情绪导致敏捷实践流于形式，无法发挥真正的作用，最终导致项目失败。

## 第五章：案例分析

### 5.1 Spotify的敏捷模型

Spotify创造了独特的"部落-小队-分会-公会"组织结构：

- **小队（Squad）**：基本的自治团队，负责特定功能
- **部落（Tribe）**：多个小队的集合，共同负责一个大的功能领域
- **分会（Chapter）**：同一专业领域的人员定期交流
- **公会（Guild）**：跨部落的兴趣小组

这种结构既保证了团队的自主性，又确保了知识的共享和传播。

### 5.2 ING银行的敏捷转型

2015年，ING银行进行了激进的敏捷转型：

1. 解散了传统的部门结构
2. 组建了跨职能的敏捷小队
3. 实施季度业务评审
4. 建立了持续学习文化

转型的结果：
- 客户满意度提升
- 产品上市时间缩短70%
- 员工参与度显著提高

## 第六章：总结与展望

敏捷不是银弹，但它提供了一种更加灵活和人性化的项目管理方式。成功的关键在于：

1. **理解精神胜于遵循形式**
2. **持续改进而非一蹴而就**
3. **文化变革重于流程改造**
4. **因地制宜而非照搬模式**

未来，随着人工智能和自动化技术的发展，敏捷方法也将继续演进，可能出现：

- AI辅助的Sprint规划
- 自动化的进度跟踪
- 智能化的风险预警
- 数据驱动的决策支持

敏捷的核心——以人为本、拥抱变化——将继续指导我们应对未来的挑战。
"""


async def test_single_dimension():
    """测试单个维度的大纲提取"""
    logger.info("开始测试单个维度的大纲提取...")
    
    outline_agent = OutlineAgent()
    
    # 测试逻辑大纲
    logger.info("\n=== 测试逻辑大纲提取 ===")
    result = await outline_agent.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "agile_pm_001",
        "dimension": OutlineDimension.LOGICAL.value
    })
    
    if result["success"]:
        logger.info("逻辑大纲提取成功！")
        logger.info(f"执行时间: {result['metadata']['duration']:.2f}秒")
        logger.info(f"Token使用量: {result['metadata']['tokens_used']}")
        
        outline_data = result["result"]
        logger.info(f"\n维度: {outline_data.get('dimension', 'logical')}")
        logger.info(f"摘要: {outline_data.get('summary', '')}")
        
        if "outline" in outline_data:
            logger.info("\n大纲内容:")
            for item in outline_data["outline"][:5]:  # 只显示前5项
                logger.info(f"  - {item}")
    else:
        logger.error(f"逻辑大纲提取失败: {result.get('error')}")


async def test_all_dimensions():
    """测试所有维度的大纲提取"""
    logger.info("\n\n=== 测试所有维度的大纲提取 ===")
    
    outline_agent = OutlineAgent()
    
    result = await outline_agent.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "agile_pm_002",
        "dimension": OutlineDimension.ALL.value
    })
    
    if result["success"]:
        logger.info("所有维度大纲提取成功！")
        logger.info(f"执行时间: {result['metadata']['duration']:.2f}秒")
        
        outline_data = result["result"]
        
        # 显示各维度的大纲
        dimensions = ["logical_outline", "thematic_outline", "temporal_outline", "causal_chain_outline"]
        
        for dim in dimensions:
            if dim in outline_data:
                logger.info(f"\n--- {dim.replace('_', ' ').title()} ---")
                items = outline_data[dim]
                if isinstance(items, list):
                    for item in items[:3]:  # 每个维度显示前3项
                        if isinstance(item, dict):
                            logger.info(f"  {item}")
                        else:
                            logger.info(f"  - {item}")
                else:
                    logger.info(f"  {items}")
    else:
        logger.error(f"所有维度大纲提取失败: {result.get('error')}")


async def test_structure_analysis():
    """测试完整的文档结构分析"""
    logger.info("\n\n=== 测试文档结构分析 ===")
    
    outline_agent = OutlineAgent()
    
    result = await outline_agent.analyze_document_structure(
        document_content=TEST_DOCUMENT,
        document_id="agile_pm_003"
    )
    
    if result["success"]:
        logger.info("文档结构分析成功！")
        
        analysis = result["result"]
        
        # 显示结构摘要
        logger.info(f"\n结构摘要: {analysis.get('structure_summary', '')}")
        
        # 显示关键洞察
        if "key_insights" in analysis:
            logger.info("\n关键洞察:")
            for insight in analysis["key_insights"]:
                logger.info(f"  • {insight}")
        
        # 显示建议
        if "recommendations" in analysis:
            logger.info("\n分析建议:")
            for rec in analysis["recommendations"]:
                logger.info(f"  → {rec}")
    else:
        logger.error(f"文档结构分析失败: {result.get('error')}")


async def test_temporal_dimension():
    """专门测试时间维度提取"""
    logger.info("\n\n=== 测试时间维度提取 ===")
    
    outline_agent = OutlineAgent()
    
    result = await outline_agent.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "agile_pm_004",
        "dimension": OutlineDimension.TEMPORAL.value
    })
    
    if result["success"]:
        logger.info("时间维度提取成功！")
        
        outline_data = result["result"]
        if "outline" in outline_data:
            logger.info("\n时间线事件:")
            for event in outline_data["outline"]:
                if isinstance(event, dict):
                    logger.info(f"  时间: {event.get('time', 'N/A')}")
                    logger.info(f"  事件: {event.get('event', 'N/A')}")
                    logger.info(f"  重要性: {event.get('importance', 'N/A')}\n")
                else:
                    logger.info(f"  - {event}")
    else:
        logger.error(f"时间维度提取失败: {result.get('error')}")


async def test_causal_dimension():
    """专门测试因果维度提取"""
    logger.info("\n\n=== 测试因果维度提取 ===")
    
    outline_agent = OutlineAgent()
    
    result = await outline_agent.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "agile_pm_005",
        "dimension": OutlineDimension.CAUSAL.value
    })
    
    if result["success"]:
        logger.info("因果维度提取成功！")
        
        outline_data = result["result"]
        if "outline" in outline_data:
            logger.info("\n因果关系链:")
            for relation in outline_data["outline"]:
                if isinstance(relation, dict):
                    logger.info(f"  原因: {relation.get('cause', 'N/A')}")
                    logger.info(f"  → 结果: {relation.get('effect', 'N/A')}")
                    logger.info(f"  强度: {relation.get('strength', 'N/A')}\n")
                else:
                    logger.info(f"  - {relation}")
    else:
        logger.error(f"因果维度提取失败: {result.get('error')}")


async def test_cache():
    """测试缓存功能"""
    logger.info("\n\n=== 测试缓存功能 ===")
    
    outline_agent = OutlineAgent()
    
    test_doc = "这是一个测试文档。它包含多个章节和主题。"
    
    # 第一次提取
    logger.info("第一次提取大纲...")
    result1 = await outline_agent.process({
        "document_content": test_doc,
        "document_id": "cache_test",
        "dimension": OutlineDimension.LOGICAL.value
    })
    
    # 第二次提取（应该从缓存读取）
    logger.info("第二次提取大纲（应该使用缓存）...")
    result2 = await outline_agent.process({
        "document_content": test_doc,
        "document_id": "cache_test",
        "dimension": OutlineDimension.LOGICAL.value
    })
    
    if result2["metadata"].get("from_cache"):
        logger.info("✓ 成功从缓存读取大纲")
        logger.info(f"  第一次耗时: {result1['metadata']['duration']:.2f}秒")
        logger.info(f"  第二次耗时: {result2['metadata']['duration']:.2f}秒")
    else:
        logger.warning("✗ 未能从缓存读取大纲")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_single_dimension())
    asyncio.run(test_all_dimensions())
    asyncio.run(test_structure_analysis())
    asyncio.run(test_temporal_dimension())
    asyncio.run(test_causal_dimension())
    asyncio.run(test_cache())