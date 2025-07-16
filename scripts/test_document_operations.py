#!/usr/bin/env python3
"""
测试文档操作功能
"""
import asyncio
import requests
from datetime import datetime

BASE_URL = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}

def test_document_operations():
    """测试文档操作API"""
    
    # 1. 获取文档列表
    print("1. 获取文档列表...")
    response = requests.get(
        f"{BASE_URL}/api/v1/documents?project_id=default&limit=5",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        documents = response.json()["items"]
        print(f"找到 {len(documents)} 个文档")
        
        if documents:
            # 使用第一个文档进行测试
            test_doc = documents[0]
            document_id = test_doc["id"]
            print(f"\n使用文档进行测试: {test_doc['filename']} (ID: {document_id})")
            
            # 2. 获取文档操作状态
            print("\n2. 获取文档操作状态...")
            response = requests.get(
                f"{BASE_URL}/api/v1/documents/{document_id}/operations/status",
                headers=HEADERS
            )
            
            if response.status_code == 200:
                status = response.json()
                print(f"文档状态: {status['document_status']}")
                print(f"操作摘要: {status['operations_summary']}")
                
                # 3. 执行摘要操作
                if not status['operations_summary']['summary_completed']:
                    print("\n3. 执行摘要生成操作...")
                    response = requests.post(
                        f"{BASE_URL}/api/v1/documents/{document_id}/operations/summary/execute",
                        headers=HEADERS
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"操作启动成功: {result['message']}")
                        print(f"管道ID: {result.get('pipeline_id')}")
                        
                        # 等待几秒查看进度
                        print("\n等待5秒后查看进度...")
                        import time
                        time.sleep(5)
                        
                        # 获取进度
                        if result.get('pipeline_id'):
                            print("\n4. 获取处理进度...")
                            response = requests.get(
                                f"{BASE_URL}/api/v2/documents/{document_id}/pipeline/{result['pipeline_id']}/progress",
                                headers=HEADERS
                            )
                            
                            if response.status_code == 200:
                                progress = response.json()
                                print(f"总体进度: {progress.get('overall_progress', 0)}%")
                                print(f"当前阶段: {progress.get('current_stage', 'N/A')}")
                                
                                # 显示各阶段状态
                                print("\n阶段详情:")
                                for stage in progress.get('stages', []):
                                    print(f"- {stage['name']}: {stage['status']} ({stage['progress']}%)")
                            else:
                                print(f"获取进度失败: {response.status_code}")
                                print(response.json())
                    else:
                        print(f"操作启动失败: {response.status_code}")
                        print(response.json())
                else:
                    print("\n摘要已经生成过了，测试索引创建...")
                    
                    # 4. 执行索引操作
                    if not status['operations_summary']['index_completed']:
                        print("\n执行索引创建操作...")
                        response = requests.post(
                            f"{BASE_URL}/api/v1/documents/{document_id}/operations/index/execute",
                            headers=HEADERS
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            print(f"索引创建启动成功: {result['message']}")
                        else:
                            print(f"索引创建失败: {response.status_code}")
                            print(response.json())
                    else:
                        print("索引也已经创建过了")
                        
                # 5. 使用通用启动API
                print("\n5. 测试通用启动API...")
                request_data = {
                    "upload_only": False,
                    "generate_summary": False,
                    "create_index": False,
                    "deep_analysis": True  # 只进行深度分析
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/documents/{document_id}/operations/start",
                    headers=HEADERS,
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"深度分析启动成功: {result['message']}")
                    print(f"预计时间: {result.get('estimated_time', 0)}秒")
                else:
                    print(f"深度分析启动失败: {response.status_code}")
                    if response.status_code == 400:
                        print("可能已有正在进行的任务")
                    print(response.json())
                    
            else:
                print(f"获取状态失败: {response.status_code}")
                print(response.json())
        else:
            print("没有找到文档，请先上传一些文档")
    else:
        print(f"获取文档列表失败: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    print("=== 文档操作功能测试 ===")
    print(f"时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}\n")
    
    test_document_operations()
    
    print("\n测试完成！")