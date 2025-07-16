#!/usr/bin/env python3
"""测试AAG知识图谱API"""

import requests
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)

# API配置
BASE_URL = "http://localhost:8200/api/v1/aag"
HEADERS = {
    "Content-Type": "application/json",
    "X-USER-ID": "u1"
}

# 测试文档
TEST_DOCUMENT = """
OpenAI和Microsoft建立了深度合作关系。Microsoft向OpenAI投资了超过100亿美元。
Sam Altman是OpenAI的CEO，他领导公司开发了ChatGPT。
ChatGPT基于GPT-4模型，这是OpenAI开发的大语言模型。
GPT-4比GPT-3.5有显著的性能提升。
"""


def test_knowledge_graph_api():
    """测试知识图谱构建API"""
    logger.info("=== 测试知识图谱构建API ===")
    
    # 1. 快速提取测试
    logger.info("\n1. 测试快速提取模式...")
    response = requests.post(
        f"{BASE_URL}/knowledge-graph",
        headers=HEADERS,
        json={
            "document_id": "test_api_doc_001",
            "document_content": TEST_DOCUMENT,
            "extraction_mode": "quick"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 快速提取成功")
            logger.info(f"  实体数: {result['result']['statistics']['total_entities']}")
            logger.info(f"  关系数: {result['result']['statistics']['total_relations']}")
            logger.info(f"  耗时: {result['metadata']['duration']:.2f}秒")
            
            # 显示实体
            logger.info("\n  提取的实体:")
            for entity in result["result"]["entities"][:5]:
                logger.info(f"    - {entity['name']} ({entity['type']})")
        else:
            logger.error(f"✗ 提取失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
        logger.error(response.text)
    
    # 2. 聚焦提取测试
    logger.info("\n2. 测试聚焦提取模式...")
    response = requests.post(
        f"{BASE_URL}/knowledge-graph",
        headers=HEADERS,
        json={
            "document_id": "test_api_doc_002",
            "document_content": TEST_DOCUMENT,
            "extraction_mode": "focused",
            "focus_types": ["person", "organization"]
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 聚焦提取成功")
            entities = result["result"]["entities"]
            persons = [e for e in entities if e["type"] == "person"]
            orgs = [e for e in entities if e["type"] == "organization"]
            logger.info(f"  人物数: {len(persons)}")
            logger.info(f"  组织数: {len(orgs)}")
        else:
            logger.error(f"✗ 提取失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_knowledge_graph_export():
    """测试知识图谱导出API"""
    logger.info("\n\n=== 测试知识图谱导出API ===")
    
    # 先构建知识图谱
    logger.info("1. 先构建知识图谱...")
    response = requests.post(
        f"{BASE_URL}/knowledge-graph",
        headers=HEADERS,
        json={
            "document_id": "test_export_doc",
            "document_content": TEST_DOCUMENT,
            "extraction_mode": "quick"
        }
    )
    
    if response.status_code == 200 and response.json()["success"]:
        logger.info("✓ 知识图谱构建成功")
        
        # 2. 导出为Neo4j格式
        logger.info("\n2. 导出为Neo4j格式...")
        response = requests.post(
            f"{BASE_URL}/knowledge-graph/export",
            headers=HEADERS,
            json={
                "document_id": "test_export_doc",
                "export_format": "neo4j"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✓ Neo4j格式导出成功")
            logger.info(f"  节点语句数: {len(result['data']['node_statements'])}")
            logger.info(f"  边语句数: {len(result['data']['edge_statements'])}")
            
            # 显示部分Cypher语句
            if result['data']['node_statements']:
                logger.info("\n  示例节点语句:")
                for stmt in result['data']['node_statements'][:2]:
                    logger.info(f"    {stmt}")
        else:
            logger.error(f"✗ 导出失败: {response.status_code}")
            logger.error(response.text)
        
        # 3. 导出为JSON格式
        logger.info("\n3. 导出为JSON格式...")
        response = requests.post(
            f"{BASE_URL}/knowledge-graph/export",
            headers=HEADERS,
            json={
                "document_id": "test_export_doc",
                "export_format": "json"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✓ JSON格式导出成功")
            logger.info(f"  实体数: {len(result['data']['entities'])}")
            logger.info(f"  关系数: {len(result['data']['relations'])}")
        else:
            logger.error(f"✗ JSON导出失败: {response.status_code}")
    else:
        logger.error("✗ 知识图谱构建失败，无法测试导出")


def test_get_artifacts():
    """测试获取分析物料API"""
    logger.info("\n\n=== 测试获取分析物料API ===")
    
    response = requests.get(
        f"{BASE_URL}/artifacts/test_api_doc_001",
        headers=HEADERS,
        params={
            "analysis_type": "knowledge_graph",
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f"✓ 获取物料成功，共 {result['total']} 个")
        
        for artifact in result["artifacts"]:
            logger.info(f"\n  物料ID: {artifact['id']}")
            logger.info(f"  分析类型: {artifact['analysis_type']}")
            logger.info(f"  深度级别: {artifact.get('depth_level', 'N/A')}")
            logger.info(f"  创建时间: {artifact['created_at']}")
    else:
        logger.error(f"✗ 获取物料失败: {response.status_code}")


def test_cache_behavior():
    """测试缓存行为"""
    logger.info("\n\n=== 测试缓存行为 ===")
    
    doc_id = "test_cache_doc"
    
    # 第一次请求
    logger.info("1. 第一次请求（无缓存）...")
    response1 = requests.post(
        f"{BASE_URL}/knowledge-graph",
        headers=HEADERS,
        json={
            "document_id": doc_id,
            "document_content": "这是一个测试文档。",
            "extraction_mode": "quick"
        }
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        if result1["success"]:
            duration1 = result1["metadata"]["duration"]
            from_cache1 = result1["metadata"].get("from_cache", False)
            logger.info(f"✓ 第一次请求成功，耗时: {duration1:.2f}秒，从缓存: {from_cache1}")
    
    # 第二次请求（应该使用缓存）
    logger.info("\n2. 第二次请求（应该使用缓存）...")
    response2 = requests.post(
        f"{BASE_URL}/knowledge-graph",
        headers=HEADERS,
        json={
            "document_id": doc_id,
            "document_content": "这是一个测试文档。",
            "extraction_mode": "quick"
        }
    )
    
    if response2.status_code == 200:
        result2 = response2.json()
        if result2["success"]:
            duration2 = result2["metadata"]["duration"]
            from_cache2 = result2["metadata"].get("from_cache", False)
            logger.info(f"✓ 第二次请求成功，耗时: {duration2:.2f}秒，从缓存: {from_cache2}")
            
            if from_cache2:
                logger.info(f"✓ 缓存生效！速度提升: {duration1/duration2:.1f}倍")
            else:
                logger.warning("✗ 缓存未生效")


if __name__ == "__main__":
    try:
        # 检查API是否可用
        response = requests.get("http://localhost:8200/health", timeout=5)
        if response.status_code != 200:
            logger.error("API服务未启动，请先启动FastAPI服务")
            sys.exit(1)
        
        # 运行测试
        test_knowledge_graph_api()
        test_knowledge_graph_export()
        test_get_artifacts()
        test_cache_behavior()
        
        logger.info("\n\n=== 所有测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        logger.error("无法连接到API服务，请确保FastAPI服务运行在 http://localhost:8200")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)