#!/usr/bin/env python3
"""测试AAG分析规划API"""

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
# 人工智能在医疗诊断中的应用研究

## 摘要

本研究探讨了深度学习技术在医疗影像诊断中的应用，特别是在肺癌早期筛查方面的突破。通过对比传统诊断方法和AI辅助诊断，我们发现AI系统能够将诊断准确率从85%提升至96.5%，同时将诊断时间从平均30分钟缩短至5分钟。

## 1. 研究背景

### 1.1 医疗诊断的挑战

- 医生资源短缺：中国每千人医生数仅为2.4人
- 诊断一致性问题：不同医生诊断结果差异可达20%
- 早期筛查困难：70%的肺癌发现时已是晚期

### 1.2 AI技术的机遇

深度学习在图像识别领域的成功为医疗诊断带来新希望：
- 卷积神经网络(CNN)在ImageNet上准确率超过人类
- 迁移学习使得医疗数据需求大幅降低
- GPU计算能力提升使实时诊断成为可能

## 2. 方法论

### 2.1 数据集

- 收集了来自10家三甲医院的50,000张胸部CT扫描
- 包含正常、早期肺癌、晚期肺癌三类
- 由3名资深放射科医生标注

### 2.2 模型架构

采用改进的ResNet-152架构：
- 添加注意力机制模块
- 多尺度特征融合
- 集成学习策略

## 3. 实验结果

### 3.1 性能指标

| 指标 | 传统方法 | AI系统 | 提升 |
|------|---------|--------|------|
| 准确率 | 85% | 96.5% | +11.5% |
| 灵敏度 | 78% | 94.2% | +16.2% |
| 特异度 | 82% | 95.8% | +13.8% |

### 3.2 时间效率

- 传统诊断：平均30分钟/例
- AI诊断：平均5分钟/例
- 效率提升：6倍

## 4. 临床验证

在实际临床应用中：
- 参与医院：5家
- 测试病例：10,000例
- 随访时间：12个月
- 误诊率降低：65%

## 5. 讨论与展望

### 5.1 技术优势

1. **准确性提升**：AI能识别人眼难以察觉的微小病变
2. **一致性保证**：消除人为主观因素
3. **效率提升**：大幅缩短诊断时间

### 5.2 存在挑战

1. **数据隐私**：患者数据保护
2. **法律责任**：AI误诊的责任归属
3. **医生接受度**：需要培训和适应期

### 5.3 未来方向

- 多模态融合：结合CT、MRI、PET等
- 个性化诊断：基于患者历史的定制模型
- 实时监测：可穿戴设备集成

## 6. 结论

AI辅助诊断系统显著提升了肺癌早期筛查的准确率和效率，但仍需解决数据隐私、法律责任等问题。建议采用人机协同的方式，将AI作为医生的辅助工具而非替代品。

## 参考文献

[包含30篇相关学术论文引用]
"""


def test_get_analysis_goals():
    """测试获取分析目标列表"""
    logger.info("=== 测试获取分析目标列表 ===")
    
    response = requests.get(
        f"{BASE_URL}/plan/goals",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        goals = response.json()["goals"]
        logger.info(f"✓ 获取到 {len(goals)} 个分析目标:")
        for goal in goals:
            logger.info(f"  - {goal['name']} ({goal['value']})")
            logger.info(f"    {goal['description']}")
            logger.info(f"    时间: {goal['typical_time']}, 成本: {goal['typical_cost']}")
    else:
        logger.error(f"✗ 获取失败: {response.status_code}")


def test_create_analysis_plan():
    """测试创建分析计划"""
    logger.info("\n=== 测试创建分析计划 ===")
    
    # 测试深度理解目标
    request_data = {
        "document_id": "medical_ai_001",
        "document_content": TEST_DOCUMENT,
        "analysis_goal": "deep_understanding",
        "user_requirements": "重点分析AI技术的准确性提升和临床应用效果",
        "time_budget": 600,
        "cost_budget": 1.0
    }
    
    response = requests.post(
        f"{BASE_URL}/plan",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 分析计划创建成功")
            plan = result["plan"]
            
            # 显示文档评估
            assessment = plan["document_assessment"]
            logger.info(f"\n文档评估:")
            logger.info(f"  类别: {assessment['category']}")
            logger.info(f"  复杂度: {assessment['complexity']}")
            logger.info(f"  质量: {assessment['quality']}")
            logger.info(f"  特征: {', '.join(assessment['key_characteristics'])}")
            
            # 显示推荐分析
            logger.info(f"\n推荐分析 ({len(plan['recommended_analyses'])}个):")
            for analysis in plan["recommended_analyses"][:5]:  # 只显示前5个
                logger.info(f"  - {analysis['analysis_type']} ({analysis['priority']})")
                logger.info(f"    预期价值: {analysis['expected_value']}")
            
            # 显示执行计划
            execution = plan["execution_plan"]
            logger.info(f"\n执行计划:")
            logger.info(f"  总时间: {execution['total_time']}秒")
            logger.info(f"  总成本: ${execution['total_cost']}")
            logger.info(f"  优化建议: {execution.get('optimization_notes', 'N/A')}")
            
            return plan  # 返回计划供后续测试使用
        else:
            logger.error(f"✗ 规划失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")
        logger.error(response.text)
    
    return None


def test_quick_overview_plan():
    """测试快速概览计划"""
    logger.info("\n=== 测试快速概览计划 ===")
    
    request_data = {
        "document_id": "medical_ai_002",
        "document_content": TEST_DOCUMENT,
        "analysis_goal": "quick_overview",
        "time_budget": 120,
        "cost_budget": 0.2
    }
    
    response = requests.post(
        f"{BASE_URL}/plan",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 快速概览计划创建成功")
            plan = result["plan"]
            
            logger.info(f"  推荐分析数: {len(plan['recommended_analyses'])}")
            logger.info(f"  总时间: {plan['execution_plan']['total_time']}秒")
            logger.info(f"  总成本: ${plan['execution_plan']['total_cost']}")
        else:
            logger.error(f"✗ 规划失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_critical_review_plan():
    """测试批判性审查计划"""
    logger.info("\n=== 测试批判性审查计划 ===")
    
    request_data = {
        "document_id": "medical_ai_003",
        "document_content": TEST_DOCUMENT,
        "analysis_goal": "critical_review",
        "user_requirements": "重点审查实验方法的科学性和结果的可靠性",
        "time_budget": 300,
        "cost_budget": 0.5
    }
    
    response = requests.post(
        f"{BASE_URL}/plan",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 批判性审查计划创建成功")
            plan = result["plan"]
            
            # 显示针对批判性审查的分析
            critical_analyses = [
                a for a in plan["recommended_analyses"] 
                if "critical" in a["analysis_type"] or "evidence" in a["analysis_type"]
            ]
            logger.info(f"  批判性分析数: {len(critical_analyses)}")
            for analysis in critical_analyses:
                logger.info(f"    - {analysis['analysis_type']}")
        else:
            logger.error(f"✗ 规划失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_progress_evaluation(plan):
    """测试进度评估"""
    logger.info("\n=== 测试进度评估 ===")
    
    if not plan:
        logger.warning("没有可用的计划进行进度评估")
        return
    
    # 模拟已完成的分析
    completed_analyses = []
    if len(plan["recommended_analyses"]) > 0:
        completed_analyses.append(plan["recommended_analyses"][0]["analysis_type"])
    if len(plan["recommended_analyses"]) > 1:
        completed_analyses.append(plan["recommended_analyses"][1]["analysis_type"])
    
    request_data = {
        "document_id": "medical_ai_001",
        "plan": plan,
        "completed_analyses": completed_analyses
    }
    
    response = requests.post(
        f"{BASE_URL}/plan/progress",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 进度评估成功")
            progress = result["progress"]
            
            logger.info(f"  完成率: {progress['completion_rate']*100:.1f}%")
            logger.info(f"  状态: {progress['status']}")
            logger.info(f"  已完成: {progress['completed_analyses']}")
            logger.info(f"  待完成数: {len(progress['pending_analyses'])}")
            
            if progress["recommendations"]:
                logger.info("  建议:")
                for rec in progress["recommendations"]:
                    logger.info(f"    - {rec}")
        else:
            logger.error(f"✗ 评估失败")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


def test_budget_constrained_plan():
    """测试预算受限的计划"""
    logger.info("\n=== 测试预算受限计划 ===")
    
    # 非常有限的预算
    request_data = {
        "document_id": "medical_ai_004",
        "document_content": TEST_DOCUMENT,
        "analysis_goal": "deep_understanding",
        "time_budget": 30,   # 只有30秒
        "cost_budget": 0.05  # 只有5分钱
    }
    
    response = requests.post(
        f"{BASE_URL}/plan",
        headers=HEADERS,
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            logger.info("✓ 预算受限计划创建成功")
            plan = result["plan"]
            
            logger.info(f"  调整后分析数: {len(plan['recommended_analyses'])}")
            logger.info(f"  实际时间: {plan['execution_plan']['total_time']}秒 (预算: 30秒)")
            logger.info(f"  实际成本: ${plan['execution_plan']['total_cost']} (预算: $0.05)")
            
            # 显示警告
            if plan.get("warnings"):
                logger.info("  警告:")
                for warning in plan["warnings"]:
                    logger.info(f"    ⚠️  {warning}")
        else:
            logger.error(f"✗ 规划失败: {result.get('error')}")
    else:
        logger.error(f"✗ API请求失败: {response.status_code}")


if __name__ == "__main__":
    try:
        # 检查API是否可用
        response = requests.get("http://localhost:8200/health", timeout=5)
        if response.status_code != 200:
            logger.error("API服务未启动，请先启动FastAPI服务")
            sys.exit(1)
        
        # 运行测试
        test_get_analysis_goals()
        plan = test_create_analysis_plan()  # 保存计划供后续使用
        test_quick_overview_plan()
        test_critical_review_plan()
        test_progress_evaluation(plan)
        test_budget_constrained_plan()
        
        logger.info("\n\n=== 所有API测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        logger.error("无法连接到API服务，请确保FastAPI服务运行在 http://localhost:8200")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)