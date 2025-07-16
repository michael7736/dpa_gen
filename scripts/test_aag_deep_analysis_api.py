#!/usr/bin/env python3
"""测试AAG深度分析API"""

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

# 测试文档 - 技术提案
TEST_DOCUMENT = """
# 区块链供应链管理系统提案

## 执行摘要

本提案旨在设计一个基于区块链的供应链管理系统，解决传统供应链中的透明度、可追溯性和信任问题。根据Gartner的研究，到2025年，30%的制造企业将使用区块链技术优化供应链。

## 1. 问题陈述

### 1.1 现状分析

当前供应链管理面临以下挑战：
- **信息孤岛**：各参与方数据不互通，导致效率低下
- **假冒伪劣**：据统计，全球假冒商品年交易额超过1.8万亿美元
- **追溯困难**：产品出现问题时，难以快速定位源头
- **信任缺失**：中介机构增加成本，延长交易时间

### 1.2 影响评估

这些问题导致：
1. 供应链效率降低20-30%（麦肯锡，2023）
2. 质量问题造成的经济损失每年超过5000亿美元
3. 消费者信心下降，品牌价值受损

## 2. 解决方案

### 2.1 技术架构

我们提出的区块链供应链系统包含：

**核心组件**：
- 许可链网络（基于Hyperledger Fabric）
- 智能合约引擎
- 分布式存储系统
- API网关

**技术特性**：
- 每秒处理10,000笔交易
- 99.99%的系统可用性
- 端到端加密保护

### 2.2 功能模块

1. **产品溯源模块**
   - 记录产品全生命周期信息
   - 支持多级供应商追踪
   - 实时更新产品状态

2. **质量认证模块**
   - 第三方认证机构接入
   - 自动验证证书真伪
   - 智能合约自动执行

3. **供应链金融模块**
   - 基于区块链的信用体系
   - 自动化支付结算
   - 降低融资成本40%

## 3. 实施计划

### 第一阶段（0-3个月）
- 完成技术选型和架构设计
- 搭建开发环境
- 开发核心功能原型

### 第二阶段（4-6个月）
- 集成主要供应商系统
- 部署试点项目
- 收集反馈并优化

### 第三阶段（7-12个月）
- 全面推广部署
- 建立运维体系
- 持续改进和扩展

## 4. 投资回报分析

### 4.1 成本估算
- 开发成本：500万美元
- 部署成本：200万美元
- 年运维成本：100万美元

### 4.2 收益预测
- 降低供应链成本15%
- 减少假冒损失80%
- 提高客户满意度25%
- 预计18个月收回投资

## 5. 风险与应对

**技术风险**：
- 风险：区块链技术不成熟
- 应对：选择成熟的企业级平台，建立技术储备

**业务风险**：
- 风险：参与方接受度低
- 应对：分阶段推进，提供培训和激励

**监管风险**：
- 风险：法规不明确
- 应对：与监管机构保持沟通，确保合规

## 6. 成功案例

沃尔玛与IBM合作的食品追溯系统：
- 将追溯时间从7天缩短到2.2秒
- 减少食品浪费30%
- 提高食品安全事件响应速度

## 7. 结论

区块链技术为供应链管理带来革命性改变。通过本方案的实施，企业可以建立透明、高效、可信的供应链体系，获得显著的竞争优势。

## 参考资料

1. Gartner (2024). "Blockchain Technology in Supply Chain Management"
2. McKinsey (2023). "The Impact of Blockchain on Supply Chain Efficiency"
3. IBM (2023). "Walmart Food Traceability Case Study"
"""


def test_evidence_chain_api():
    """测试证据链分析API"""
    logger.info("=== 测试证据链分析API ===")
    
    # 准备请求数据
    request_data = {
        "document_id": "blockchain_proposal_001",
        "document_content": TEST_DOCUMENT,
        "focus_claims": [
            "30%的制造企业将使用区块链技术",
            "全球假冒商品年交易额超过1.8万亿美元",
            "将追溯时间从7天缩短到2.2秒"
        ]
    }
    
    # 发送请求
    response = requests.post(
        f"{BASE_URL}/deep-analysis/evidence-chain",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 证据链分析成功")
            logger.info(f"  耗时: {result['metadata']['duration']:.2f}秒")
            logger.info(f"  Token使用: {result['metadata']['tokens_used']}")
            
            # 显示部分结果
            evidence_chain = result["analyses"]["evidence_chain"]
            if "claims" in evidence_chain:
                logger.info(f"  分析的声明数: {len(evidence_chain['claims'])}")
            if "overall_assessment" in evidence_chain:
                assessment = evidence_chain["overall_assessment"]
                logger.info(f"  证据完整性: {assessment.get('evidence_completeness')}/10")
        else:
            logger.error(f"✗ 分析失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
        logger.error(response.text)


def test_cross_reference_api():
    """测试交叉引用分析API"""
    logger.info("\n=== 测试交叉引用分析API ===")
    
    # 准备请求数据
    request_data = {
        "document_id": "blockchain_proposal_002",
        "document_content": TEST_DOCUMENT
    }
    
    # 发送请求
    response = requests.post(
        f"{BASE_URL}/deep-analysis/cross-reference",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 交叉引用分析成功")
            logger.info(f"  耗时: {result['metadata']['duration']:.2f}秒")
            
            cross_ref = result["analyses"]["cross_reference"]
            if "consistency_analysis" in cross_ref:
                consistency = cross_ref["consistency_analysis"]
                logger.info(f"  术语一致性: {consistency.get('terminology_consistency')}/10")
                logger.info(f"  逻辑一致性: {consistency.get('logical_consistency')}/10")
        else:
            logger.error(f"✗ 分析失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_critical_thinking_api():
    """测试批判性思维分析API"""
    logger.info("\n=== 测试批判性思维分析API ===")
    
    # 准备请求数据
    request_data = {
        "document_id": "blockchain_proposal_003",
        "document_content": TEST_DOCUMENT,
        "analysis_depth": "comprehensive"
    }
    
    # 发送请求
    response = requests.post(
        f"{BASE_URL}/deep-analysis/critical-thinking",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 批判性思维分析成功")
            logger.info(f"  耗时: {result['metadata']['duration']:.2f}秒")
            logger.info(f"  分析深度: {result['metadata'].get('analysis_depth')}")
            
            critical = result["analyses"]["critical_thinking"]
            if "critical_assessment" in critical:
                assessment = critical["critical_assessment"]
                logger.info(f"  逻辑严密性: {assessment.get('logical_rigor')}/10")
                logger.info(f"  客观性: {assessment.get('objectivity')}/10")
        else:
            logger.error(f"✗ 分析失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_comprehensive_deep_analysis():
    """测试综合深度分析API"""
    logger.info("\n=== 测试综合深度分析API ===")
    
    # 准备请求数据
    request_data = {
        "document_id": "blockchain_proposal_all",
        "document_content": TEST_DOCUMENT,
        "analysis_types": [
            "evidence_chain",
            "cross_reference", 
            "critical_thinking"
        ],
        "focus_claims": ["降低供应链成本15%"],
        "analysis_depth": "deep"
    }
    
    # 发送请求
    response = requests.post(
        f"{BASE_URL}/deep-analysis",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 综合深度分析成功")
            logger.info(f"  总耗时: {result['metadata']['duration']:.2f}秒")
            logger.info(f"  总Token使用: {result['metadata']['tokens_used']}")
            logger.info(f"  完成的分析数: {result['metadata']['analysis_count']}")
            
            # 显示各分析的状态
            for analysis_type, analysis_result in result["analyses"].items():
                status = "成功" if "error" not in analysis_result else "失败"
                logger.info(f"  {analysis_type}: {status}")
        else:
            logger.error(f"✗ 分析失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
        logger.error(response.text[:500])


def test_partial_analysis():
    """测试部分深度分析"""
    logger.info("\n=== 测试部分深度分析 ===")
    
    # 只执行证据链和批判性思维分析
    request_data = {
        "document_id": "blockchain_proposal_partial",
        "document_content": TEST_DOCUMENT,
        "analysis_types": ["evidence_chain", "critical_thinking"],
        "analysis_depth": "basic"
    }
    
    response = requests.post(
        f"{BASE_URL}/deep-analysis",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 部分深度分析成功")
            logger.info(f"  执行的分析类型: {list(result['analyses'].keys())}")
        else:
            logger.error(f"✗ 分析失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_cache_behavior():
    """测试缓存行为"""
    logger.info("\n=== 测试缓存行为 ===")
    
    doc_id = "cache_test_api"
    doc_content = "这是缓存测试文档。包含声明：系统性能提升50%。"
    
    # 第一次请求
    logger.info("1. 第一次请求（无缓存）...")
    response1 = requests.post(
        f"{BASE_URL}/deep-analysis/evidence-chain",
        headers=HEADERS,
        json={
            "document_id": doc_id,
            "document_content": doc_content
        }
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        if result1["success"]:
            duration1 = result1["metadata"]["duration"]
            logger.info(f"  第一次请求耗时: {duration1:.2f}秒")
    
    # 第二次请求
    logger.info("\n2. 第二次请求（应该使用缓存）...")
    response2 = requests.post(
        f"{BASE_URL}/deep-analysis/evidence-chain",
        headers=HEADERS,
        json={
            "document_id": doc_id,
            "document_content": doc_content
        }
    )
    
    if response2.status_code == 200:
        result2 = response2.json()
        if result2["success"]:
            duration2 = result2["metadata"]["duration"]
            from_cache = result2["metadata"].get("from_cache", False)
            logger.info(f"  第二次请求耗时: {duration2:.2f}秒")
            logger.info(f"  是否使用缓存: {from_cache}")
            
            if from_cache and duration1 > 0:
                logger.info(f"  速度提升: {duration1/max(duration2, 0.001):.1f}倍")


if __name__ == "__main__":
    try:
        # 检查API是否可用
        response = requests.get("http://localhost:8200/health", timeout=5)
        if response.status_code != 200:
            logger.error("API服务未启动，请先启动FastAPI服务")
            sys.exit(1)
        
        # 运行测试
        test_evidence_chain_api()
        test_cross_reference_api()
        test_critical_thinking_api()
        test_comprehensive_deep_analysis()
        test_partial_analysis()
        test_cache_behavior()
        
        logger.info("\n\n=== 所有API测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        logger.error("无法连接到API服务，请确保FastAPI服务运行在 http://localhost:8200")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)