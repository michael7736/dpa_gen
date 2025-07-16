#!/usr/bin/env python3
"""
测试AAG编排引擎API端点
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# API配置
BASE_URL = "http://localhost:8200/api/v1/aag"
HEADERS = {
    "X-USER-ID": "u1",
    "Content-Type": "application/json"
}

# 测试文档
TEST_DOCUMENT = """
# 量子计算的商业应用前景分析

## 摘要
量子计算作为下一代计算技术，正在从实验室走向商业应用。本报告分析了量子计算在金融、医药、物流和密码学等领域的潜在应用，评估了技术成熟度和商业化进程，并对未来5-10年的发展趋势进行了预测。

## 1. 技术现状

### 1.1 硬件发展
当前量子计算机主要有三种技术路线：
- 超导量子比特（IBM、Google采用）
- 离子阱（IonQ、Honeywell采用）
- 拓扑量子比特（Microsoft研究中）

2023年，IBM发布了1121量子比特的Condor处理器，标志着量子计算进入了新的发展阶段。

### 1.2 软件生态
量子编程框架日趋成熟：
- Qiskit（IBM）
- Cirq（Google）
- Q#（Microsoft）
- PennyLane（Xanadu）

## 2. 商业应用场景

### 2.1 金融行业
- 投资组合优化：量子算法可以在更短时间内找到最优投资组合
- 风险分析：量子蒙特卡洛方法提升风险计算效率
- 欺诈检测：量子机器学习增强异常检测能力

### 2.2 制药行业
- 分子模拟：精确模拟药物分子与靶点的相互作用
- 药物发现：加速新药筛选过程
- 个性化医疗：优化治疗方案

### 2.3 物流优化
- 路径规划：解决复杂的旅行商问题
- 供应链优化：实时优化库存和配送

## 3. 商业化挑战

### 3.1 技术挑战
- 量子退相干：量子比特的稳定性问题
- 错误率：当前量子计算机错误率仍然较高
- 可扩展性：增加量子比特数量面临工程挑战

### 3.2 商业挑战
- 高昂成本：量子计算机的建设和维护成本极高
- 人才短缺：量子计算专业人才稀缺
- 应用开发：将理论算法转化为实际应用需要时间

## 4. 市场预测
根据BCG的研究，量子计算市场规模预计：
- 2025年：50亿美元
- 2030年：250亿美元
- 2040年：8500亿美元

## 5. 结论与建议
量子计算正处于从实验室到商业应用的关键转折期。企业应该：
1. 开始评估量子计算对自身业务的潜在影响
2. 投资量子计算人才培养
3. 与量子计算公司建立合作关系
4. 准备量子安全的加密方案

未来5年将是量子计算商业化的关键窗口期，先行者将获得显著的竞争优势。
"""


async def test_get_workflow_templates():
    """测试获取工作流模板"""
    print("\n=== 测试获取工作流模板 ===")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/workflow/templates",
            headers=HEADERS
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("可用的工作流模板:")
                for template in data["templates"]:
                    print(f"\n模板ID: {template['id']}")
                    print(f"名称: {template['name']}")
                    print(f"描述: {template['description']}")
                    print(f"预计时间: {template['estimated_time']}")
                    print(f"组件: {', '.join(template['components'])}")
            else:
                print(f"请求失败: {response.status}")
                print(await response.text())


async def test_create_workflow_from_template(template_id):
    """测试基于模板创建工作流"""
    print(f"\n=== 测试基于模板 {template_id} 创建工作流 ===")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/workflow/template/{template_id}/create",
            headers=HEADERS
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"创建成功: {data['message']}")
                print(f"工作流ID: {data['workflow_id']}")
                return data['workflow_id']
            else:
                print(f"请求失败: {response.status}")
                print(await response.text())
                return None


async def test_execute_workflow(workflow_id, document_id):
    """测试执行工作流"""
    print(f"\n=== 测试执行工作流 {workflow_id} ===")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/workflow/{workflow_id}/execute",
            headers=HEADERS,
            json={
                "document_id": document_id,
                "initial_state": {
                    "test_mode": True
                }
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get("task_id"):
                    print(f"工作流已提交到后台执行")
                    print(f"任务ID: {data['task_id']}")
                else:
                    print(f"工作流执行成功!")
                    print(f"执行路径: {data.get('execution_path', [])}")
                    print(f"完成步骤: {data.get('metadata', {}).get('completed_steps', 0)}")
                    print(f"执行时间: {data.get('metadata', {}).get('duration', 0):.2f}秒")
                    
                    # 显示部分结果
                    artifacts = data.get("artifacts", {})
                    if artifacts:
                        print("\n部分分析结果:")
                        for name, content in list(artifacts.items())[:2]:
                            print(f"\n{name}:")
                            print(json.dumps(content, ensure_ascii=False, indent=2)[:500] + "...")
                
                return data
            else:
                print(f"请求失败: {response.status}")
                print(await response.text())
                return None


async def test_create_custom_workflow():
    """测试创建自定义工作流"""
    print("\n=== 测试创建自定义工作流 ===")
    
    workflow_data = {
        "workflow_id": f"custom_workflow_{int(datetime.now().timestamp())}",
        "name": "量子计算商业分析工作流",
        "description": "专门分析量子计算商业应用的工作流"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/workflow/create",
            headers=HEADERS,
            json=workflow_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"创建成功: {data['message']}")
                print(f"工作流ID: {data['workflow_id']}")
                return data['workflow_id']
            else:
                print(f"请求失败: {response.status}")
                print(await response.text())
                return None


async def test_with_real_document():
    """使用真实文档测试工作流"""
    print("\n=== 使用真实文档测试 ===")
    
    # 首先需要上传文档
    async with aiohttp.ClientSession() as session:
        # 这里假设文档已经上传，直接使用文档ID
        # 在实际测试中，需要先通过文档上传API上传文档
        
        # 创建标准分析工作流
        workflow_id = await test_create_workflow_from_template("standard_analysis")
        
        if workflow_id:
            # 执行工作流（使用模拟的文档ID）
            await test_execute_workflow(workflow_id, "quantum_computing_doc_001")


async def main():
    """主测试函数"""
    try:
        # 1. 获取工作流模板
        await test_get_workflow_templates()
        
        # 2. 基于模板创建工作流
        standard_workflow_id = await test_create_workflow_from_template("standard_analysis")
        critical_workflow_id = await test_create_workflow_from_template("critical_review")
        adaptive_workflow_id = await test_create_workflow_from_template("adaptive_analysis")
        
        # 3. 创建自定义工作流
        custom_workflow_id = await test_create_custom_workflow()
        
        # 4. 执行工作流（需要先通过文档API上传文档）
        # 这里使用模拟的文档ID进行测试
        if standard_workflow_id:
            await test_execute_workflow(standard_workflow_id, "test_doc_standard")
        
        if critical_workflow_id:
            await test_execute_workflow(critical_workflow_id, "test_doc_critical")
        
        if adaptive_workflow_id:
            await test_execute_workflow(adaptive_workflow_id, "test_doc_adaptive")
        
        print("\n=== API测试完成 ===")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("AAG编排引擎API测试")
    print("确保API服务运行在 http://localhost:8200")
    print("=" * 50)
    
    asyncio.run(main())