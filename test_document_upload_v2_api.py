import requests
import json
import time
from pathlib import Path

# API配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"  # 使用u1，后端会自动转换为UUID
PROJECT_ID = "default"

def test_document_upload_v2():
    """测试文档上传V2 API"""
    
    # 1. 准备测试文件
    test_file = "/Users/mdwong001/Desktop/code/rag/data/zonghe/Start research.pdf"
    if not Path(test_file).exists():
        print(f"测试文件不存在: {test_file}")
        # 创建一个测试文本文件
        test_file = "test_document.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("这是一个测试文档，用于验证AAG系统的智能上传V2功能。\n\n")
            f.write("# 测试内容\n\n")
            f.write("本文档包含一些测试文本，用于验证：\n")
            f.write("1. 文件上传功能\n")
            f.write("2. 文档处理功能\n")
            f.write("3. 索引创建功能\n")
            f.write("4. 摘要生成功能\n")
    
    print(f"使用测试文件: {test_file}")
    
    # 2. 准备上传数据
    with open(test_file, "rb") as f:
        files = {"file": (Path(test_file).name, f, "application/pdf")}
        
        # 处理选项
        processing_options = {
            "upload_only": True,
            "generate_summary": True,
            "create_index": True,
            "deep_analysis": False
        }
        
        # 构建请求
        headers = {"X-USER-ID": USER_ID}
        params = {"project_id": PROJECT_ID}
        data = {"options": json.dumps(processing_options)}
        
        print("\n发送上传请求...")
        print(f"URL: {BASE_URL}/api/v1/documents/upload/v2")
        print(f"Headers: {headers}")
        print(f"Params: {params}")
        print(f"Processing Options: {processing_options}")
        
        # 3. 发送请求
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/documents/upload/v2",
                headers=headers,
                params=params,
                files=files,
                data=data
            )
            
            print(f"\n响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\n上传成功!")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # 检查处理管道
                if result.get("processing_pipeline"):
                    pipeline = result["processing_pipeline"]
                    print(f"\n处理管道ID: {pipeline['pipeline_id']}")
                    print(f"文档ID: {result['document_id']}")
                    
                    # 轮询处理进度
                    print("\n开始监控处理进度...")
                    monitor_processing_progress(
                        result['document_id'],
                        pipeline['pipeline_id'],
                        headers
                    )
                else:
                    print("\n仅上传模式，没有处理管道")
                    
            else:
                print("\n上传失败!")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"\n请求失败: {str(e)}")
            import traceback
            traceback.print_exc()


def monitor_processing_progress(document_id, pipeline_id, headers):
    """监控处理进度"""
    url = f"{BASE_URL}/api/v1/documents/{document_id}/pipeline/{pipeline_id}/progress"
    
    max_attempts = 60  # 最多等待60秒
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                progress = response.json()
                print(f"\r进度: {progress['overall_progress']:.1f}% - {progress.get('current_stage', 'N/A')}", end="")
                
                if progress.get("completed"):
                    print("\n\n处理完成!")
                    print("\n各阶段耗时:")
                    for stage in progress["stages"]:
                        if stage.get("duration"):
                            print(f"- {stage['name']}: {stage['duration']:.1f}秒")
                    break
                    
                if progress.get("interrupted") or progress.get("failed"):
                    print(f"\n\n处理失败或中断: {progress}")
                    break
                    
            time.sleep(1)
            attempt += 1
            
        except Exception as e:
            print(f"\n获取进度失败: {str(e)}")
            break
    
    if attempt >= max_attempts:
        print("\n\n处理超时!")


if __name__ == "__main__":
    print("=== 测试文档上传V2 API ===")
    test_document_upload_v2()