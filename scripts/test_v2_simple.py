#!/usr/bin/env python3
"""
简单测试新的文档处理流程 V2
"""

import requests
import time
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
    content = """# 测试文档

这是一个用于测试文档处理V2的简单文档。

## 主要内容
- 测试文档上传
- 测试摘要生成
- 测试索引创建

## 结论
这个文档用于验证新的处理流程是否正常工作。
"""
    
    file_path = Path("test_doc.md")
    file_path.write_text(content, encoding='utf-8')
    return file_path


def test_upload_only():
    """测试仅上传"""
    print("\n=== 测试1: 仅上传 ===")
    
    file_path = create_test_file()
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/markdown')}
            data = {
                'upload_only': 'true',
                'generate_summary': 'false',
                'create_index': 'false',
                'deep_analysis': 'false'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v2/documents/upload",
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 上传成功!")
            print(f"  文档ID: {result['document_id']}")
            print(f"  状态: {result['status']}")
            print(f"  消息: {result['message']}")
        else:
            print(f"✗ 上传失败: {response.text}")
            
    finally:
        file_path.unlink()


def test_upload_with_summary():
    """测试上传并生成摘要"""
    print("\n=== 测试2: 上传并生成摘要 ===")
    
    file_path = create_test_file()
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/markdown')}
            data = {
                'upload_only': 'false',
                'generate_summary': 'true',
                'create_index': 'false',
                'deep_analysis': 'false'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v2/documents/upload",
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 上传成功!")
            print(f"  文档ID: {result['document_id']}")
            print(f"  状态: {result['status']}")
            
            if result.get('processing_pipeline'):
                pipeline = result['processing_pipeline']
                print(f"  管道ID: {pipeline['pipeline_id']}")
                print("  处理阶段:")
                for stage in pipeline['stages']:
                    print(f"    - {stage['name']}: {stage['status']}")
                    
                # 等待并检查进度
                print("\n检查处理进度...")
                time.sleep(5)
                
                progress_url = f"{BASE_URL}/api/v2/documents/{result['document_id']}/pipeline/{pipeline['pipeline_id']}/progress"
                progress_response = requests.get(progress_url, headers=headers)
                
                if progress_response.status_code == 200:
                    progress = progress_response.json()
                    print(f"总进度: {progress['overall_progress']}%")
                    for stage in progress['stages']:
                        print(f"  - {stage['name']}: {stage['status']} ({stage['progress']}%)")
        else:
            print(f"✗ 上传失败: {response.text}")
            
    finally:
        file_path.unlink()


def main():
    """主函数"""
    print("=== 文档处理 V2 简单测试 ===")
    
    # 测试仅上传
    test_upload_only()
    
    # 测试上传并生成摘要
    test_upload_with_summary()
    
    print("\n测试完成!")


if __name__ == "__main__":
    main()