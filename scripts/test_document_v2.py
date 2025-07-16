#!/usr/bin/env python3
"""
测试新的文档处理流程 V2
测试用户选择处理选项功能
"""

import asyncio
import requests
import time
import json
from pathlib import Path

# API配置
BASE_URL = "http://localhost:8200"
USER_ID = "243588ff-459d-45b8-b77b-09aec3946a64"  # default_user

# 请求头
headers = {
    "X-USER-ID": USER_ID
}


def create_test_file():
    """创建测试文件"""
    content = """# 人工智能在医疗领域的应用研究

## 摘要
本文探讨了人工智能（AI）技术在医疗保健领域的最新应用和发展趋势。随着深度学习、自然语言处理和计算机视觉技术的快速发展，AI正在革新医疗诊断、治疗方案制定和患者护理等多个方面。

## 1. 引言
医疗保健行业正经历着前所未有的数字化转型。人工智能作为这一转型的核心驱动力，正在重塑医疗服务的提供方式。从早期诊断到个性化治疗，AI技术展现出巨大的潜力。

## 2. AI在医疗诊断中的应用

### 2.1 医学影像分析
深度学习算法在医学影像分析中表现出色，特别是在以下领域：
- 肿瘤检测：AI系统能够识别早期癌症征兆
- 眼科疾病：糖尿病视网膜病变的自动筛查
- 放射学：胸部X光片异常检测

### 2.2 病理学诊断
数字病理学结合AI技术，提高了诊断的准确性和效率。

## 3. 个性化医疗

### 3.1 基因组学分析
AI帮助解析复杂的基因组数据，实现精准医疗。

### 3.2 药物研发
机器学习加速新药发现过程，降低研发成本。

## 4. 挑战与展望

### 4.1 数据隐私和安全
医疗数据的敏感性要求严格的隐私保护措施。

### 4.2 监管和伦理
AI医疗应用需要完善的监管框架。

## 5. 结论
人工智能正在成为医疗保健领域不可或缺的工具。随着技术的不断进步和应用的深入，我们有理由相信AI将继续推动医疗行业的创新和发展。

## 参考文献
[1] Smith, J. et al. (2024). "AI in Healthcare: A Comprehensive Review"
[2] Zhang, L. et al. (2024). "Deep Learning for Medical Image Analysis"
[3] Brown, K. et al. (2023). "Ethical Considerations in AI-driven Healthcare"
"""
    
    # 保存到文件
    file_path = Path("test_medical_ai.md")
    file_path.write_text(content, encoding='utf-8')
    return file_path


def test_upload_with_options(file_path, options):
    """测试带选项的文档上传"""
    print(f"\n测试上传文档，选项: {options}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'text/markdown')}
        data = {
            'upload_only': str(options.get('upload_only', False)).lower(),
            'generate_summary': str(options.get('generate_summary', False)).lower(),
            'create_index': str(options.get('create_index', False)).lower(),
            'deep_analysis': str(options.get('deep_analysis', False)).lower()
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/documents/upload",
            files=files,
            data=data,
            headers=headers
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 上传成功!")
        print(f"  文档ID: {result['document_id']}")
        print(f"  文件名: {result['filename']}")
        print(f"  大小: {result['size']} bytes")
        print(f"  状态: {result['status']}")
        
        if result.get('processing_pipeline'):
            print(f"  管道ID: {result['processing_pipeline']['pipeline_id']}")
            print("  处理阶段:")
            for stage in result['processing_pipeline']['stages']:
                print(f"    - {stage['name']}: {stage['status']}")
        
        return result
    else:
        print(f"✗ 上传失败: {response.status_code}")
        print(f"  错误: {response.text}")
        return None


def check_pipeline_progress(document_id, pipeline_id):
    """检查管道进度"""
    print(f"\n检查处理进度...")
    
    url = f"{BASE_URL}/api/v2/documents/{document_id}/pipeline/{pipeline_id}/progress"
    
    # 持续检查进度直到完成
    while True:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            progress = response.json()
            print(f"\r总进度: {progress['overall_progress']:.1f}%", end='')
            
            # 显示当前阶段
            if progress['current_stage']:
                print(f" | 当前阶段: {progress['current_stage']}", end='')
            
            # 检查是否完成或中断
            if progress['overall_progress'] >= 100 or progress['interrupted']:
                print()  # 换行
                
                # 显示各阶段详情
                print("\n各阶段状态:")
                for stage in progress['stages']:
                    status_icon = "✓" if stage['status'] == "completed" else "⏳" if stage['status'] == "processing" else "⏸" if stage['status'] == "interrupted" else "○"
                    print(f"  {status_icon} {stage['name']}: {stage['progress']}%")
                    if stage.get('message'):
                        print(f"     {stage['message']}")
                    if stage.get('duration'):
                        print(f"     耗时: {stage['duration']:.1f}秒")
                
                break
            
            time.sleep(2)  # 每2秒检查一次
        else:
            print(f"\n✗ 获取进度失败: {response.status_code}")
            break


def test_interrupt_and_resume(document_id, pipeline_id):
    """测试中断和恢复功能"""
    print(f"\n测试中断处理...")
    
    # 中断处理
    response = requests.post(
        f"{BASE_URL}/api/v2/documents/{document_id}/pipeline/{pipeline_id}/interrupt",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ 成功中断处理")
        
        # 等待几秒
        print("等待3秒后恢复...")
        time.sleep(3)
        
        # 恢复处理
        response = requests.post(
            f"{BASE_URL}/api/v2/documents/{document_id}/pipeline/{pipeline_id}/resume",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ 成功恢复处理")
        else:
            print(f"✗ 恢复失败: {response.text}")
    else:
        print(f"✗ 中断失败: {response.text}")


def main():
    """主测试函数"""
    print("=== 文档处理 V2 测试 ===")
    
    # 创建测试文件
    file_path = create_test_file()
    print(f"创建测试文件: {file_path}")
    
    # 测试1：仅上传
    print("\n--- 测试1: 仅上传 ---")
    result1 = test_upload_with_options(file_path, {
        'upload_only': True
    })
    
    # 测试2：上传并生成摘要
    print("\n--- 测试2: 上传并生成摘要 ---")
    result2 = test_upload_with_options(file_path, {
        'generate_summary': True
    })
    
    if result2 and result2.get('processing_pipeline'):
        check_pipeline_progress(
            result2['document_id'],
            result2['processing_pipeline']['pipeline_id']
        )
    
    # 测试3：上传、摘要、索引
    print("\n--- 测试3: 上传、摘要、索引 ---")
    result3 = test_upload_with_options(file_path, {
        'generate_summary': True,
        'create_index': True
    })
    
    if result3 and result3.get('processing_pipeline'):
        # 测试中断和恢复
        time.sleep(5)  # 等待处理开始
        test_interrupt_and_resume(
            result3['document_id'],
            result3['processing_pipeline']['pipeline_id']
        )
        
        # 继续检查进度
        check_pipeline_progress(
            result3['document_id'],
            result3['processing_pipeline']['pipeline_id']
        )
    
    # 测试4：全部处理选项
    print("\n--- 测试4: 全部处理选项 ---")
    result4 = test_upload_with_options(file_path, {
        'generate_summary': True,
        'create_index': True,
        'deep_analysis': True
    })
    
    if result4 and result4.get('processing_pipeline'):
        check_pipeline_progress(
            result4['document_id'],
            result4['processing_pipeline']['pipeline_id']
        )
    
    # 清理测试文件
    file_path.unlink()
    print("\n测试完成!")


if __name__ == "__main__":
    main()