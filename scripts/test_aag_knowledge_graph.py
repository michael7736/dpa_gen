#!/usr/bin/env python3
"""测试AAG知识图谱构建功能"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aag.agents import KnowledgeGraphAgent, EntityType, RelationType
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文档内容 - 一篇关于人工智能公司的文章
TEST_DOCUMENT = """
# DeepMind和OpenAI：AI领域的双雄

## 公司背景

DeepMind是一家英国的人工智能公司，成立于2010年，由Demis Hassabis、Shane Legg和Mustafa Suleyman共同创立。2014年，Google以约4亿英镑的价格收购了DeepMind。该公司总部位于伦敦，专注于通用人工智能（AGI）的研究。

OpenAI则是一家美国的人工智能研究实验室，成立于2015年，由Elon Musk、Sam Altman、Greg Brockman等人共同创立。OpenAI最初是一个非营利组织，后来成立了营利性子公司OpenAI LP。总部位于旧金山。

## 核心技术

### DeepMind的突破

1. **AlphaGo**：2016年，DeepMind开发的AlphaGo击败了世界围棋冠军李世石，这是AI历史上的里程碑事件。AlphaGo使用深度学习和蒙特卡洛树搜索技术。

2. **AlphaFold**：2020年，DeepMind发布的AlphaFold在蛋白质结构预测方面取得重大突破，解决了生物学界50年的难题。该系统使用了创新的神经网络架构。

3. **Gemini**：2023年发布的多模态AI模型，能够理解和生成文本、图像、音频、视频和代码。

### OpenAI的创新

1. **GPT系列**：从GPT-1到GPT-4，OpenAI在大语言模型领域不断突破。GPT-3拥有1750亿参数，而GPT-4的能力更加强大。

2. **ChatGPT**：2022年11月发布的ChatGPT引发了全球AI热潮，仅5天就突破100万用户。它基于GPT-3.5和GPT-4模型。

3. **DALL-E**：文本到图像的生成模型，能够根据文字描述创建高质量的图像。DALL-E 2和DALL-E 3不断提升生成质量。

## 商业模式对比

DeepMind作为Google（Alphabet）的子公司，主要通过内部研发支持Google的产品和服务。其研究成果应用于Google搜索、Google助手、YouTube等产品。

OpenAI采用混合模式，通过API服务、ChatGPT Plus订阅、企业解决方案等方式盈利。与微软建立了深度合作关系，微软投资超过100亿美元。

## 研究理念

DeepMind强调科学研究和长期目标，致力于解决智能的本质问题。他们的研究涵盖强化学习、神经科学、机器学习等多个领域。

OpenAI的使命是确保通用人工智能（AGI）造福全人类。他们强调AI安全性和对齐问题，同时也注重商业化应用。

## 主要人物

- **Demis Hassabis**（DeepMind CEO）：神经科学家、计算机科学家、游戏设计师
- **Sam Altman**（OpenAI CEO）：企业家、投资人，Y Combinator前总裁
- **Ilya Sutskever**（OpenAI首席科学家）：深度学习先驱，Geoffrey Hinton的学生
- **Geoffrey Hinton**：深度学习之父，曾在Google和多伦多大学工作

## 影响与展望

这两家公司正在塑造AI的未来。DeepMind在科学研究方面不断突破，而OpenAI在产品化和商业化方面领先。它们的竞争与合作推动着整个AI行业的发展。

未来，随着AGI的逐步实现，这两家公司将在AI安全、伦理和治理方面扮演重要角色。
"""


async def test_quick_extraction():
    """测试快速提取模式"""
    logger.info("开始测试快速提取模式...")
    
    kg_agent = KnowledgeGraphAgent()
    
    result = await kg_agent.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "ai_companies_001",
        "extraction_mode": "quick"
    })
    
    if result["success"]:
        logger.info("快速提取成功！")
        logger.info(f"执行时间: {result['metadata']['duration']:.2f}秒")
        logger.info(f"Token使用量: {result['metadata']['tokens_used']}")
        
        kg_data = result["result"]
        stats = kg_data["statistics"]
        
        logger.info("\n=== 统计信息 ===")
        logger.info(f"实体总数: {stats['total_entities']}")
        logger.info(f"关系总数: {stats['total_relations']}")
        logger.info(f"平均节点度: {stats['average_node_degree']:.2f}")
        
        logger.info("\n=== 实体类型分布 ===")
        for entity_type, count in stats["entity_type_distribution"].items():
            logger.info(f"  {entity_type}: {count}")
        
        logger.info("\n=== 核心实体 ===")
        for core_entity in stats.get("core_entities", []):
            logger.info(f"  {core_entity['name']} (度数: {core_entity['degree']})")
        
        # 显示部分实体
        logger.info("\n=== 部分实体示例 ===")
        for entity in kg_data["entities"][:5]:
            logger.info(f"  {entity['name']} ({entity['type']})")
            
    else:
        logger.error(f"快速提取失败: {result.get('error')}")


async def test_focused_extraction():
    """测试聚焦提取模式"""
    logger.info("\n\n=== 测试聚焦提取模式 ===")
    
    kg_agent = KnowledgeGraphAgent()
    
    # 只提取人物和组织
    result = await kg_agent.process({
        "document_content": TEST_DOCUMENT,
        "document_id": "ai_companies_002",
        "extraction_mode": "focused",
        "focus_types": ["person", "organization"]
    })
    
    if result["success"]:
        logger.info("聚焦提取成功！")
        
        kg_data = result["result"]
        logger.info(f"\n找到 {len(kg_data['entities'])} 个人物和组织实体")
        
        # 按类型分组显示
        persons = [e for e in kg_data["entities"] if e["type"] == "person"]
        orgs = [e for e in kg_data["entities"] if e["type"] == "organization"]
        
        logger.info(f"\n人物 ({len(persons)}):")
        for person in persons:
            logger.info(f"  - {person['name']}")
        
        logger.info(f"\n组织 ({len(orgs)}):")
        for org in orgs:
            logger.info(f"  - {org['name']}")
            
    else:
        logger.error(f"聚焦提取失败: {result.get('error')}")


async def test_comprehensive_extraction():
    """测试全面提取模式"""
    logger.info("\n\n=== 测试全面提取模式 ===")
    
    kg_agent = KnowledgeGraphAgent()
    
    # 使用较短的文档测试
    short_doc = TEST_DOCUMENT[:2000]  # 只使用前2000字符
    
    result = await kg_agent.process({
        "document_content": short_doc,
        "document_id": "ai_companies_003",
        "extraction_mode": "comprehensive"
    })
    
    if result["success"]:
        logger.info("全面提取成功！")
        
        kg_data = result["result"]
        stats = kg_data["statistics"]
        
        logger.info(f"\n实体总数: {stats['total_entities']}")
        logger.info(f"关系总数: {stats['total_relations']}")
        
        # 显示关系类型分布
        logger.info("\n=== 关系类型分布 ===")
        for rel_type, count in stats["relation_type_distribution"].items():
            logger.info(f"  {rel_type}: {count}")
        
        # 显示一些关系示例
        logger.info("\n=== 关系示例 ===")
        entity_id_to_name = {e["id"]: e["name"] for e in kg_data["entities"]}
        
        for rel in kg_data["relations"][:5]:
            source_name = entity_id_to_name.get(rel["source"], rel["source"])
            target_name = entity_id_to_name.get(rel["target"], rel["target"])
            logger.info(f"  {source_name} --[{rel['type']}]--> {target_name}")
            
    else:
        logger.error(f"全面提取失败: {result.get('error')}")


async def test_neo4j_export():
    """测试Neo4j导出功能"""
    logger.info("\n\n=== 测试Neo4j导出功能 ===")
    
    kg_agent = KnowledgeGraphAgent()
    
    # 先进行快速提取
    result = await kg_agent.process({
        "document_content": TEST_DOCUMENT[:1000],
        "document_id": "ai_companies_export",
        "extraction_mode": "quick"
    })
    
    if result["success"]:
        kg_data = result["result"]
        entities = kg_data["entities"]
        relations = kg_data["relations"]
        
        # 导出为Neo4j格式
        export_data = await kg_agent.export_to_neo4j_format(entities, relations)
        
        logger.info("Neo4j导出成功！")
        logger.info(f"节点语句数: {len(export_data['node_statements'])}")
        logger.info(f"边语句数: {len(export_data['edge_statements'])}")
        
        # 显示部分Cypher语句
        logger.info("\n=== 部分Cypher语句示例 ===")
        for stmt in export_data['node_statements'][:3]:
            logger.info(stmt)
        
        if export_data['edge_statements']:
            logger.info("\n边语句示例:")
            for stmt in export_data['edge_statements'][:2]:
                logger.info(stmt)
    else:
        logger.error("提取失败，无法测试导出功能")


async def test_cache():
    """测试缓存功能"""
    logger.info("\n\n=== 测试缓存功能 ===")
    
    kg_agent = KnowledgeGraphAgent()
    
    test_doc = "OpenAI开发了ChatGPT。Sam Altman是OpenAI的CEO。"
    
    # 第一次提取
    logger.info("第一次提取...")
    result1 = await kg_agent.process({
        "document_content": test_doc,
        "document_id": "cache_test",
        "extraction_mode": "quick"
    })
    
    # 第二次提取（应该从缓存读取）
    logger.info("第二次提取（应该使用缓存）...")
    result2 = await kg_agent.process({
        "document_content": test_doc,
        "document_id": "cache_test",
        "extraction_mode": "quick"
    })
    
    if result2["metadata"].get("from_cache"):
        logger.info("✓ 成功从缓存读取知识图谱")
        logger.info(f"  第一次耗时: {result1['metadata']['duration']:.2f}秒")
        logger.info(f"  第二次耗时: {result2['metadata']['duration']:.2f}秒")
    else:
        logger.warning("✗ 未能从缓存读取知识图谱")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_quick_extraction())
    asyncio.run(test_focused_extraction())
    asyncio.run(test_comprehensive_extraction())
    asyncio.run(test_neo4j_export())
    asyncio.run(test_cache())