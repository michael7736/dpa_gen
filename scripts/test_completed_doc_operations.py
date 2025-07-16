#!/usr/bin/env python3
"""
测试已完成文档的操作功能
"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}

def test_completed_document():
    """测试已完成文档的操作API"""
    
    # 使用已完成的文档
    document_id = "71760317-d7a7-433b-bac1-a3d49fd66891"  # test_doc3.md
    
    print(f"测试文档: test_doc3.md (ID: {document_id})")
    
    # 1. 获取文档操作状态
    print("\n1. 获取文档操作状态...")
    response = requests.get(
        f"{BASE_URL}/api/v1/documents/{document_id}/operations/status",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        status = response.json()
        print(f"文档状态: {status['document_status']}")
        print(f"操作摘要: {status['operations_summary']}")
        
        # 显示处理历史
        if status.get('processing_history'):
            print("\n处理历史:")
            for history in status['processing_history']:
                print(f"- {history['operation']}: {history['status']} "
                      f"(开始: {history.get('started_at', 'N/A')}, "
                      f"完成: {history.get('completed_at', 'N/A')})")
                if history.get('message'):
                    print(f"  消息: {history['message']}")
                if history.get('error'):
                    print(f"  错误: {history['error']}")
        
        # 2. 测试重新执行操作
        print("\n2. 测试重新执行摘要生成...")
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{document_id}/operations/summary/execute",
            headers=HEADERS
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
        
    else:
        print(f"获取状态失败: {response.status_code}")
        print(response.json())

def test_new_document_upload():
    """测试新文档上传"""
    print("\n\n=== 测试新文档上传 ===")
    
    # 创建测试文件
    import tempfile
    import os
    
    content = """# 测试文档操作功能

这是一个用于测试文档操作功能的测试文档。

## 测试内容

1. 文档上传
2. 摘要生成
3. 索引创建
4. 深度分析

## 测试时间

创建时间: """ + str(datetime.now())
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        # 上传文件（仅上传，不处理）
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_operations_demo.md', f, 'text/markdown')}
            data = {
                'upload_only': 'true',
                'generate_summary': 'false',
                'create_index': 'false',
                'deep_analysis': 'false'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v2/documents/upload?project_id=default",
                headers=HEADERS,
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"文档上传成功!")
                print(f"文档ID: {result['document_id']}")
                print(f"文件名: {result['filename']}")
                return result['document_id']
            else:
                print(f"上传失败: {response.status_code}")
                print(response.json())
                return None
    finally:
        os.unlink(temp_file)

if __name__ == "__main__":
    print("=== 文档操作功能详细测试 ===")
    print(f"时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}\n")
    
    # 测试已完成的文档
    test_completed_document()
    
    # 上传新文档并测试
    new_doc_id = test_new_document_upload()
    if new_doc_id:
        print(f"\n使用新上传的文档 {new_doc_id} 进行操作测试...")
        # 这里可以添加对新文档的操作测试
    
    print("\n测试完成！")