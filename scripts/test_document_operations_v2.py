#!/usr/bin/env python3
"""
测试文档操作功能 - 增强版
"""
import asyncio
import requests
from datetime import datetime
import time

BASE_URL = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}

def test_document_operations():
    """测试文档操作API"""
    
    # 1. 获取文档列表
    print("1. 获取文档列表...")
    response = requests.get(
        f"{BASE_URL}/api/v1/documents?project_id=default&limit=10",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        documents = response.json()["items"]
        print(f"找到 {len(documents)} 个文档")
        
        # 显示所有文档状态
        print("\n文档列表:")
        for doc in documents:
            print(f"- {doc['filename']} (ID: {doc['id']}, 状态: {doc['status']})")
        
        # 找一个未处理或已完成的文档
        test_doc = None
        for doc in documents:
            if doc['status'] in ['uploaded', 'completed']:
                test_doc = doc
                break
        
        if not test_doc:
            print("\n没有找到可测试的文档(状态为uploaded或completed)")
            return
            
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
            
            # 显示处理历史
            if status.get('processing_history'):
                print("\n处理历史:")
                for history in status['processing_history']:
                    print(f"- {history['operation']}: {history['status']} ({history.get('message', 'N/A')})")
            
            # 3. 执行单独操作
            operations = []
            if not status['operations_summary']['summary_completed']:
                operations.append('summary')
            if not status['operations_summary']['index_completed']:
                operations.append('index')
            if not status['operations_summary']['analysis_completed']:
                operations.append('analysis')
            
            if operations:
                print(f"\n3. 需要执行的操作: {', '.join(operations)}")
                
                # 执行第一个未完成的操作
                operation = operations[0]
                print(f"\n执行 {operation} 操作...")
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/documents/{document_id}/operations/{operation}/execute",
                    headers=HEADERS
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"操作启动成功: {result['message']}")
                    
                    if result.get('pipeline_id'):
                        print(f"管道ID: {result['pipeline_id']}")
                        
                        # 监控进度5次
                        print("\n监控处理进度...")
                        for i in range(5):
                            time.sleep(2)
                            
                            # 获取进度
                            progress_response = requests.get(
                                f"{BASE_URL}/api/v2/documents/{document_id}/pipeline/{result['pipeline_id']}/progress",
                                headers=HEADERS
                            )
                            
                            if progress_response.status_code == 200:
                                progress = progress_response.json()
                                print(f"\n[{i+1}/5] 总体进度: {progress.get('overall_progress', 0)}%")
                                print(f"当前阶段: {progress.get('current_stage', 'N/A')}")
                                
                                # 显示各阶段状态
                                for stage in progress.get('stages', []):
                                    status_emoji = "✓" if stage['status'] == 'completed' else "⏳" if stage['status'] == 'in_progress' else "○"
                                    print(f"  {status_emoji} {stage['name']}: {stage['progress']}%")
                                
                                if progress.get('completed'):
                                    print("\n处理完成！")
                                    break
                            else:
                                print(f"获取进度失败: {progress_response.status_code}")
                else:
                    print(f"操作启动失败: {response.status_code}")
                    print(response.json())
            else:
                print("\n所有操作都已完成！")
                
            # 4. 测试中断和恢复功能
            print("\n4. 测试通用启动API（可中断）...")
            request_data = {
                "upload_only": False,
                "generate_summary": True,
                "create_index": True,
                "deep_analysis": True
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/documents/{document_id}/operations/start",
                headers=HEADERS,
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"处理启动成功: {result['message']}")
                print(f"预计时间: {result.get('estimated_time', 0)}秒")
                
                if result.get('pipeline_id'):
                    # 等待3秒后尝试中断
                    print("\n等待3秒后尝试中断...")
                    time.sleep(3)
                    
                    # 中断处理
                    interrupt_response = requests.post(
                        f"{BASE_URL}/api/v1/documents/{document_id}/operations/interrupt",
                        headers=HEADERS,
                        json={"pipeline_id": result['pipeline_id']}
                    )
                    
                    if interrupt_response.status_code == 200:
                        print("成功中断处理！")
                        
                        # 等待2秒后恢复
                        print("\n等待2秒后恢复处理...")
                        time.sleep(2)
                        
                        resume_response = requests.post(
                            f"{BASE_URL}/api/v1/documents/{document_id}/operations/resume",
                            headers=HEADERS,
                            json={"pipeline_id": result['pipeline_id']}
                        )
                        
                        if resume_response.status_code == 200:
                            print("成功恢复处理！")
                        else:
                            print(f"恢复失败: {resume_response.status_code}")
                            print(resume_response.json())
                    else:
                        print(f"中断失败: {interrupt_response.status_code}")
                        print(interrupt_response.json())
            else:
                print(f"处理启动失败: {response.status_code}")
                if response.status_code == 400:
                    print("可能已有正在进行的任务或所有操作已完成")
                print(response.json())
                
        else:
            print(f"获取状态失败: {response.status_code}")
            print(response.json())
    else:
        print(f"获取文档列表失败: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    print("=== 文档操作功能测试（增强版） ===")
    print(f"时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}\n")
    
    test_document_operations()
    
    print("\n测试完成！")