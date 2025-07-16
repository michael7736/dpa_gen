#!/usr/bin/env python3
"""测试AAG API端点"""

import asyncio
import httpx
import json
from pathlib import Path

# API配置
BASE_URL = "http://localhost:8000"
USER_ID = "u1"  # 默认用户ID

# 测试文档内容
TEST_DOCUMENT = """
# 人工智能的未来：机遇与挑战

## 引言

人工智能（AI）正在以前所未有的速度改变着我们的世界。从自动驾驶汽车到智能语音助手，
从医疗诊断到金融风控，AI技术已经渗透到社会生活的方方面面。

## 主要发展趋势

### 1. 大模型时代
近年来，以GPT、BERT为代表的大规模预训练模型展现出了惊人的能力。这些模型通过在海量
数据上进行训练，学习到了丰富的语言知识和推理能力。

### 2. 多模态融合
AI正在从单一模态向多模态发展，能够同时处理文本、图像、音频等多种信息。

### 3. 边缘计算
随着物联网的发展，越来越多的AI计算正在向边缘设备迁移，实现更快的响应速度和更好的隐私保护。

## 面临的挑战

1. **伦理问题**：AI决策的公平性、透明性和可解释性
2. **安全风险**：对抗攻击、数据泄露等安全威胁
3. **就业影响**：自动化可能导致的工作岗位变化
4. **监管难题**：如何制定合理的AI治理框架

## 结论

人工智能的发展前景广阔，但也需要我们审慎对待其带来的挑战。只有在技术创新与社会责任
之间找到平衡，才能让AI真正造福人类。
"""


async def test_skim_api():
    """测试快速略读API"""
    print("=== 测试AAG快速略读API ===\n")
    
    async with httpx.AsyncClient() as client:
        # 准备请求数据
        request_data = {
            "document_id": "test_doc_001",
            "document_content": TEST_DOCUMENT,
            "document_type": "技术文章"
        }
        
        # 发送请求
        headers = {"X-USER-ID": USER_ID}
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/aag/skim",
                json=request_data,
                headers=headers,
                timeout=30.0
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result["success"]:
                    skim_result = result["result"]
                    print(f"\n文档类型: {skim_result.get('document_type')}")
                    print(f"核心主题: {skim_result.get('core_topic')}")
                    
                    print("\n关键要点:")
                    for i, point in enumerate(skim_result.get('key_points', []), 1):
                        print(f"  {i}. {point}")
                    
                    quality = skim_result.get('quality_assessment', {})
                    print(f"\n质量评估: {quality.get('level')} - {quality.get('reason')}")
                else:
                    print(f"略读失败: {result.get('error')}")
            else:
                print(f"请求失败: {response.text}")
                
        except httpx.TimeoutException:
            print("请求超时")
        except Exception as e:
            print(f"请求异常: {str(e)}")


async def test_get_artifacts():
    """测试获取分析物料API"""
    print("\n\n=== 测试获取分析物料API ===\n")
    
    async with httpx.AsyncClient() as client:
        headers = {"X-USER-ID": USER_ID}
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/aag/artifacts/test_doc_001",
                headers=headers,
                params={"analysis_type": "skim"}
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"找到 {result['total']} 个物料")
                
                for artifact in result.get("artifacts", []):
                    print(f"\n物料ID: {artifact['id']}")
                    print(f"分析类型: {artifact['analysis_type']}")
                    print(f"创建时间: {artifact['created_at']}")
                    print(f"Token使用量: {artifact.get('token_usage')}")
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"请求异常: {str(e)}")


async def test_get_metadata():
    """测试获取文档元数据API"""
    print("\n\n=== 测试获取文档元数据API ===\n")
    
    async with httpx.AsyncClient() as client:
        headers = {"X-USER-ID": USER_ID}
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/aag/metadata/test_doc_001",
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                metadata = response.json()
                print(f"元数据: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
            elif response.status_code == 404:
                print("元数据不存在")
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"请求异常: {str(e)}")


async def main():
    """运行所有测试"""
    print("开始测试AAG API端点...\n")
    
    # 测试略读API
    await test_skim_api()
    
    # 测试获取物料API
    await test_get_artifacts()
    
    # 测试获取元数据API
    await test_get_metadata()
    
    print("\n\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())