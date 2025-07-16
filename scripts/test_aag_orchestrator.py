#!/usr/bin/env python3
"""
测试AAG编排引擎
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime

from src.aag.engines import OrchestrationEngine, WorkflowNode, WorkflowEdge, ExecutionMode
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 测试文档
TEST_DOCUMENT = """
# 人工智能在医疗诊断中的应用研究

## 摘要
本研究探讨了人工智能（AI）技术在医疗诊断领域的应用现状和未来发展趋势。通过对2018-2023年间发表的150篇相关文献进行系统综述，我们发现AI在医学影像诊断、病理分析和临床决策支持等方面取得了显著进展。研究表明，深度学习模型在某些特定疾病的诊断准确率已经达到或超过了人类专家水平，特别是在皮肤癌、糖尿病视网膜病变和肺结节检测方面。

## 1. 引言
人工智能技术的快速发展为医疗诊断带来了革命性的变化。传统的医疗诊断依赖于医生的经验和知识，存在主观性强、效率低下等问题。AI技术的引入不仅可以提高诊断的准确性和效率，还能够帮助解决医疗资源分布不均的问题。

## 2. AI在医疗诊断中的主要应用

### 2.1 医学影像诊断
深度学习，特别是卷积神经网络（CNN）在医学影像分析中表现出色。例如，Google的研究团队开发的AI系统在检测糖尿病视网膜病变方面的准确率达到了90.3%，超过了许多眼科专家。

### 2.2 病理分析
AI在病理切片分析中的应用日益广泛。斯坦福大学的研究人员开发的算法能够以91%的准确率区分皮肤癌和良性病变，这一准确率与21位认证皮肤科医生的平均水平相当。

### 2.3 临床决策支持
IBM Watson for Oncology等AI系统通过分析大量的医学文献、治疗指南和患者数据，为医生提供个性化的治疗建议。在纪念斯隆-凯特琳癌症中心的研究中，Watson在肺癌治疗方案推荐上与肿瘤专家的一致率达到了96%。

## 3. 挑战与限制

### 3.1 数据质量和隐私
高质量的标注数据是训练AI模型的基础。然而，医疗数据的获取和标注成本高昂，且涉及患者隐私保护的法律和伦理问题。

### 3.2 可解释性
深度学习模型的"黑箱"特性使得医生难以理解AI做出诊断的依据，这在医疗领域尤其成问题，因为医生需要对诊断结果负责。

### 3.3 监管和标准化
目前缺乏统一的AI医疗产品审批标准和监管框架，这阻碍了AI技术在临床的广泛应用。

## 4. 未来展望
随着技术的不断进步和监管框架的完善，AI在医疗诊断中的应用前景广阔。未来的发展方向包括：
- 多模态数据融合
- 联邦学习保护隐私
- 可解释AI技术
- 人机协作诊断模式

## 5. 结论
AI技术在医疗诊断中展现出巨大潜力，但仍需解决数据、可解释性和监管等挑战。通过持续的技术创新和跨学科合作，AI有望成为医生的得力助手，共同提升医疗服务质量。
"""


async def test_create_workflow():
    """测试创建工作流"""
    print("\n=== 测试创建工作流 ===")
    
    engine = OrchestrationEngine()
    
    # 创建自定义工作流
    workflow_id = engine.create_workflow(
        workflow_id="test_custom_workflow",
        name="测试自定义工作流",
        description="用于测试的自定义分析工作流"
    )
    
    print(f"创建工作流成功: {workflow_id}")
    
    # 添加节点
    engine.add_node(workflow_id, WorkflowNode(
        name="quick_skim",
        agent_type="skimmer"
    ))
    
    engine.add_node(workflow_id, WorkflowNode(
        name="outline_extraction",
        agent_type="outline",
        agent_config={"dimension": "logical"},
        dependencies=["quick_skim"]
    ))
    
    engine.add_node(workflow_id, WorkflowNode(
        name="summary_generation",
        agent_type="summarizer",
        agent_config={"summary_level": "level_3"},
        dependencies=["quick_skim"]
    ))
    
    # 添加边
    engine.add_edge(workflow_id, WorkflowEdge("quick_skim", "outline_extraction"))
    engine.add_edge(workflow_id, WorkflowEdge("quick_skim", "summary_generation"))
    
    print("节点和边添加完成")
    
    return engine, workflow_id


async def test_standard_workflow():
    """测试标准分析工作流"""
    print("\n=== 测试标准分析工作流 ===")
    
    engine = OrchestrationEngine()
    
    # 创建标准工作流
    workflow_id = engine.create_standard_analysis_workflow()
    print(f"创建标准工作流: {workflow_id}")
    
    # 执行工作流
    result = await engine.execute_workflow(
        workflow_id=workflow_id,
        document_id="test_doc_001",
        document_content=TEST_DOCUMENT
    )
    
    if result["success"]:
        print(f"工作流执行成功!")
        print(f"执行路径: {result['execution_path']}")
        print(f"完成步骤数: {result['metadata']['completed_steps']}")
        print(f"执行时间: {result['metadata']['duration']:.2f}秒")
        print(f"错误数: {result['metadata']['errors']}")
        
        # 显示部分结果
        artifacts = result.get("artifacts", {})
        if "skim" in artifacts:
            print(f"\n略读结果:")
            print(f"  文档类型: {artifacts['skim'].get('document_type')}")
            print(f"  核心价值: {artifacts['skim'].get('core_value')}")
            print(f"  质量评估: {artifacts['skim'].get('quality_assessment', {}).get('level')}")
    else:
        print(f"工作流执行失败: {result.get('error')}")
    
    return result


async def test_critical_review_workflow():
    """测试批判性审查工作流"""
    print("\n=== 测试批判性审查工作流 ===")
    
    engine = OrchestrationEngine()
    
    # 创建批判性审查工作流
    workflow_id = engine.create_critical_review_workflow()
    print(f"创建批判性审查工作流: {workflow_id}")
    
    # 执行工作流
    result = await engine.execute_workflow(
        workflow_id=workflow_id,
        document_id="test_doc_002",
        document_content=TEST_DOCUMENT
    )
    
    if result["success"]:
        print(f"工作流执行成功!")
        print(f"执行路径: {result['execution_path']}")
        print(f"完成步骤数: {result['metadata']['completed_steps']}")
        print(f"执行时间: {result['metadata']['duration']:.2f}秒")
        
        # 显示深度分析结果
        artifacts = result.get("artifacts", {})
        if "deep_analysis" in artifacts:
            print(f"\n深度分析结果:")
            analyses = artifacts["deep_analysis"]
            
            if "evidence_chain" in analyses:
                print(f"  证据链分析:")
                print(f"    声明数量: {len(analyses['evidence_chain'].get('claims', []))}")
                print(f"    总体质量: {analyses['evidence_chain'].get('overall_quality', {}).get('score')}")
            
            if "critical_thinking" in analyses:
                print(f"  批判性思维分析:")
                print(f"    逻辑谬误: {len(analyses['critical_thinking'].get('logical_fallacies', []))}")
                print(f"    隐含假设: {len(analyses['critical_thinking'].get('assumptions', []))}")
    else:
        print(f"工作流执行失败: {result.get('error')}")
    
    return result


async def test_adaptive_workflow():
    """测试自适应工作流"""
    print("\n=== 测试自适应工作流 ===")
    
    engine = OrchestrationEngine()
    
    # 创建自适应工作流
    workflow_id = engine.create_adaptive_workflow()
    print(f"创建自适应工作流: {workflow_id}")
    
    # 执行工作流
    result = await engine.execute_workflow(
        workflow_id=workflow_id,
        document_id="test_doc_003",
        document_content=TEST_DOCUMENT
    )
    
    if result["success"]:
        print(f"工作流执行成功!")
        print(f"执行路径: {result['execution_path']}")
        print(f"完成步骤数: {result['metadata']['completed_steps']}")
        print(f"执行时间: {result['metadata']['duration']:.2f}秒")
        
        # 检查是否根据文档质量选择了不同的分析路径
        execution_path = result['execution_path']
        if "deep_summary" in execution_path:
            print("文档质量高，执行了深度分析")
        elif "quick_summary" in execution_path:
            print("文档质量一般，执行了快速分析")
    else:
        print(f"工作流执行失败: {result.get('error')}")
    
    return result


async def main():
    """主测试函数"""
    try:
        # 测试创建自定义工作流
        engine, workflow_id = await test_create_workflow()
        
        # 执行自定义工作流
        print("\n=== 执行自定义工作流 ===")
        result = await engine.execute_workflow(
            workflow_id=workflow_id,
            document_id="test_doc_custom",
            document_content=TEST_DOCUMENT
        )
        
        if result["success"]:
            print(f"自定义工作流执行成功!")
            print(f"执行路径: {result['execution_path']}")
        else:
            print(f"自定义工作流执行失败: {result.get('error')}")
        
        # 测试预定义工作流
        await test_standard_workflow()
        await test_critical_review_workflow()
        await test_adaptive_workflow()
        
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())