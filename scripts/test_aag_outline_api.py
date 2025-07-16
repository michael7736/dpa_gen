#!/usr/bin/env python3
"""测试AAG多维大纲API"""

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

# 测试文档 - 技术文档示例
TEST_DOCUMENT = """
# 微服务架构设计指南

## 1. 概述

微服务架构是一种将应用程序构建为一组小型服务的方法，每个服务运行在其自己的进程中，并通过轻量级机制（通常是HTTP API）进行通信。

### 1.1 发展历史

- 2011年：术语"微服务"首次出现
- 2014年：Martin Fowler发表关键文章
- 2015年：Netflix公开其微服务实践
- 2016年：容器技术成熟，推动微服务普及
- 2018年：Service Mesh概念兴起
- 2020年：云原生成为主流

### 1.2 核心原则

1. **单一职责**：每个服务只负责一个业务功能
2. **自治性**：服务独立部署和扩展
3. **去中心化**：数据和决策分散
4. **容错性**：故障隔离和优雅降级

## 2. 架构模式

### 2.1 API网关模式

API网关作为所有客户端的单一入口点，提供：
- 请求路由
- 认证授权
- 限流熔断
- 协议转换

**因果关系**：统一入口 → 简化客户端 → 降低耦合 → 提高可维护性

### 2.2 服务发现模式

服务实例动态注册和发现，支持：
- 客户端发现（Eureka）
- 服务端发现（AWS ELB）
- 混合模式

**影响链**：服务注册 → 动态发现 → 负载均衡 → 高可用性

## 3. 实施步骤

### 第一阶段：评估和规划（第1-4周）
- 现有系统分析
- 服务边界识别
- 技术栈选择
- 团队培训

### 第二阶段：试点项目（第5-12周）
- 选择低风险服务
- 构建CI/CD流水线
- 实施监控体系
- 收集反馈优化

### 第三阶段：逐步迁移（第13-24周）
- 按优先级拆分服务
- 数据库解耦
- 建立服务治理
- 性能调优

### 第四阶段：全面推广（第25周后）
- 推广最佳实践
- 完善工具链
- 建立标准规范
- 持续改进

## 4. 关键技术

### 4.1 容器化（Docker/Kubernetes）
容器提供了一致的运行环境，Kubernetes提供了编排能力。

### 4.2 服务网格（Istio/Linkerd）
处理服务间通信的基础设施层，提供流量管理、安全、可观测性。

### 4.3 分布式追踪（Jaeger/Zipkin）
跟踪请求在多个服务间的调用链路，帮助排查性能问题。

## 5. 挑战与解决方案

### 5.1 分布式事务
**问题**：跨服务的数据一致性
**解决**：Saga模式、事件溯源

### 5.2 网络延迟
**问题**：服务间调用增加延迟
**解决**：服务合并、缓存策略、异步通信

### 5.3 运维复杂度
**问题**：服务数量增加导致管理困难
**解决**：自动化工具、统一监控、标准化流程

## 6. 总结

微服务不是银弹，需要根据实际情况权衡利弊。成功的关键在于：
- 合理的服务划分
- 完善的基础设施
- 成熟的团队文化
- 持续的演进优化
"""


def test_outline_api():
    """测试大纲提取API"""
    logger.info("=== 测试大纲提取API ===")
    
    # 1. 测试逻辑维度
    logger.info("\n1. 测试逻辑维度提取...")
    response = requests.post(
        f"{BASE_URL}/outline",
        headers=HEADERS,
        json={
            "document_id": "microservice_guide_001",
            "document_content": TEST_DOCUMENT,
            "dimension": "logical"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 逻辑维度提取成功")
            logger.info(f"  维度: {result['result'].get('dimension', 'N/A')}")
            logger.info(f"  摘要: {result['result'].get('summary', 'N/A')}")
            logger.info(f"  耗时: {result['metadata']['duration']:.2f}秒")
        else:
            logger.error(f"✗ 提取失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
        logger.error(response.text)
    
    # 2. 测试主题维度
    logger.info("\n2. 测试主题维度提取...")
    response = requests.post(
        f"{BASE_URL}/outline",
        headers=HEADERS,
        json={
            "document_id": "microservice_guide_002",
            "document_content": TEST_DOCUMENT,
            "dimension": "thematic"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 主题维度提取成功")
            outline = result["result"].get("outline", [])
            logger.info(f"  主题数量: {len(outline)}")
            if outline:
                logger.info("  主要主题:")
                for theme in outline[:3]:
                    if isinstance(theme, dict):
                        logger.info(f"    - {theme.get('theme', theme)}")
                    else:
                        logger.info(f"    - {theme}")
        else:
            logger.error(f"✗ 提取失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
    
    # 3. 测试时间维度
    logger.info("\n3. 测试时间维度提取...")
    response = requests.post(
        f"{BASE_URL}/outline",
        headers=HEADERS,
        json={
            "document_id": "microservice_guide_003",
            "document_content": TEST_DOCUMENT,
            "dimension": "temporal"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 时间维度提取成功")
            outline = result["result"].get("outline", [])
            logger.info(f"  时间点数量: {len(outline)}")
        else:
            logger.error(f"✗ 提取失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
    
    # 4. 测试因果维度
    logger.info("\n4. 测试因果维度提取...")
    response = requests.post(
        f"{BASE_URL}/outline",
        headers=HEADERS,
        json={
            "document_id": "microservice_guide_004",
            "document_content": TEST_DOCUMENT,
            "dimension": "causal"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 因果维度提取成功")
            outline = result["result"].get("outline", [])
            logger.info(f"  因果关系数量: {len(outline)}")
        else:
            logger.error(f"✗ 提取失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_all_dimensions():
    """测试提取所有维度"""
    logger.info("\n\n=== 测试提取所有维度 ===")
    
    response = requests.post(
        f"{BASE_URL}/outline",
        headers=HEADERS,
        json={
            "document_id": "microservice_guide_all",
            "document_content": TEST_DOCUMENT,
            "dimension": "all"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 所有维度提取成功")
            logger.info(f"  耗时: {result['metadata']['duration']:.2f}秒")
            logger.info(f"  Token使用: {result['metadata']['tokens_used']}")
            
            outline_data = result["result"]
            dimensions = ["logical_outline", "thematic_outline", 
                         "temporal_outline", "causal_chain_outline"]
            
            for dim in dimensions:
                if dim in outline_data:
                    logger.info(f"\n  {dim.replace('_', ' ').title()}:")
                    items = outline_data[dim]
                    if isinstance(items, list) and items:
                        logger.info(f"    包含 {len(items)} 个项目")
        else:
            logger.error(f"✗ 提取失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
        logger.error(response.text)


def test_structure_analysis():
    """测试文档结构分析"""
    logger.info("\n\n=== 测试文档结构分析 ===")
    
    response = requests.post(
        f"{BASE_URL}/outline/structure-analysis",
        headers=HEADERS,
        json={
            "document_id": "microservice_guide_structure",
            "document_content": TEST_DOCUMENT
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 结构分析成功")
            
            analysis = result["analysis"]
            
            # 显示结构摘要
            logger.info(f"\n结构摘要: {analysis.get('structure_summary', 'N/A')}")
            
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
            logger.error(f"✗ 分析失败")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
        logger.error(response.text)


def test_cache_behavior():
    """测试缓存行为"""
    logger.info("\n\n=== 测试缓存行为 ===")
    
    doc_id = "cache_test_outline"
    test_content = "这是缓存测试文档。包含简单的结构和内容。"
    
    # 第一次请求
    logger.info("1. 第一次请求（无缓存）...")
    response1 = requests.post(
        f"{BASE_URL}/outline",
        headers=HEADERS,
        json={
            "document_id": doc_id,
            "document_content": test_content,
            "dimension": "logical"
        }
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        if result1["success"]:
            duration1 = result1["metadata"]["duration"]
            from_cache1 = result1["metadata"].get("from_cache", False)
            logger.info(f"✓ 第一次请求成功，耗时: {duration1:.2f}秒，从缓存: {from_cache1}")
    
    # 第二次请求
    logger.info("\n2. 第二次请求（应该使用缓存）...")
    response2 = requests.post(
        f"{BASE_URL}/outline",
        headers=HEADERS,
        json={
            "document_id": doc_id,
            "document_content": test_content,
            "dimension": "logical"
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
        test_outline_api()
        test_all_dimensions()
        test_structure_analysis()
        test_cache_behavior()
        
        logger.info("\n\n=== 所有测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        logger.error("无法连接到API服务，请确保FastAPI服务运行在 http://localhost:8200")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)