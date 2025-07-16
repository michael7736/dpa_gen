#!/usr/bin/env python3
"""
文档结果查看工具
使用方法：
python view_results.py summary <document_id>    # 查看摘要
python view_results.py status <document_id>     # 查看状态
python view_results.py analysis <document_id>   # 查看分析
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1"}

def format_datetime(dt_str):
    """格式化时间显示"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str

def view_summary(document_id):
    """查看文档摘要"""
    print(f"📖 查看文档摘要 (ID: {document_id})")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/documents/{document_id}/summary", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            print(f"📄 文档名称: {data['filename']}")
            print(f"🕒 生成时间: {format_datetime(data['generated_at'])}")
            print(f"📝 文档ID: {data['document_id']}")
            print("\n📋 摘要内容:")
            print("-" * 30)
            print(data['summary'])
            print("-" * 30)
        else:
            print(f"❌ 获取摘要失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def view_status(document_id):
    """查看文档处理状态"""
    print(f"📊 查看文档状态 (ID: {document_id})")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/documents/{document_id}/operations/status", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            
            print(f"📄 文档ID: {data['document_id']}")
            print(f"📝 文档状态: {data['document_status']}")
            print(f"🔄 是否有活跃任务: {'是' if data['has_active_pipeline'] else '否'}")
            
            print("\n📋 操作摘要:")
            ops = data['operations_summary']
            print(f"  ✅ 摘要生成: {'已完成' if ops['summary_completed'] else '未完成'}")
            print(f"  🔍 索引创建: {'已完成' if ops['index_completed'] else '未完成'}")
            print(f"  🧠 深度分析: {'已完成' if ops['analysis_completed'] else '未完成'}")
            
            if data['pipelines']:
                print(f"\n🔧 处理管道 ({len(data['pipelines'])}个):")
                for i, pipeline in enumerate(data['pipelines'], 1):
                    print(f"\n  管道 {i}:")
                    print(f"    ID: {pipeline['pipeline_id']}")
                    print(f"    创建时间: {format_datetime(pipeline['created_at'])}")
                    print(f"    总体进度: {pipeline['overall_progress']:.1f}%")
                    print(f"    当前阶段: {pipeline['current_stage']}")
                    print(f"    是否完成: {'是' if pipeline['completed'] else '否'}")
                    print(f"    是否中断: {'是' if pipeline['interrupted'] else '否'}")
                    
                    if pipeline['stages']:
                        print(f"    阶段详情:")
                        for stage in pipeline['stages']:
                            status_icon = {
                                'completed': '✅',
                                'processing': '⏳',
                                'pending': '⌛',
                                'failed': '❌'
                            }.get(stage['status'], '❓')
                            
                            duration_text = ""
                            if stage.get('duration'):
                                duration_text = f" ({stage['duration']:.1f}s)"
                            
                            print(f"      {status_icon} {stage['name']}: {stage['status']} ({stage['progress']}%){duration_text}")
                            if stage.get('message'):
                                print(f"        消息: {stage['message']}")
        else:
            print(f"❌ 获取状态失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def view_analysis(document_id):
    """查看分析结果"""
    print(f"🧠 查看深度分析结果 (ID: {document_id})")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/documents/{document_id}/analysis", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            
            print(f"📄 分析ID: {data['analysis_id']}")
            print(f"📝 文档ID: {data['document_id']}")
            print(f"🔍 分析深度: {data['analysis_depth']}")
            print(f"📊 状态: {data['status']}")
            print(f"🕒 创建时间: {format_datetime(data['created_at'])}")
            
            result = data.get('result', {})
            
            if result.get('executive_summary'):
                print(f"\n📋 执行摘要:")
                print("-" * 30)
                print(result['executive_summary'])
                print("-" * 30)
            
            if result.get('key_insights'):
                print(f"\n💡 关键洞察:")
                for i, insight in enumerate(result['key_insights'], 1):
                    print(f"  {i}. {insight}")
            
            if result.get('action_items'):
                print(f"\n🎯 行动建议:")
                for i, item in enumerate(result['action_items'], 1):
                    print(f"  {i}. {item}")
                    
        else:
            print(f"❌ 获取分析结果失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def list_documents():
    """列出可用文档"""
    print("📚 可用文档列表")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/documents?project_id=e1900ad1-f1a1-4e80-8796-9c45c7e124a5&limit=10", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                for i, doc in enumerate(data['items'], 1):
                    print(f"{i}. {doc['filename']}")
                    print(f"   ID: {doc['id']}")
                    print(f"   状态: {doc['status']}")
                    print(f"   大小: {doc['file_size']} bytes")
                    print()
            else:
                print("没有找到文档")
        else:
            print(f"❌ 获取文档列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def main():
    if len(sys.argv) < 2:
        print("📖 文档结果查看工具")
        print("\n使用方法:")
        print("  python view_results.py list                    # 列出文档")
        print("  python view_results.py summary <document_id>   # 查看摘要")
        print("  python view_results.py status <document_id>    # 查看状态")
        print("  python view_results.py analysis <document_id>  # 查看分析")
        print("\n示例:")
        print("  python view_results.py summary 4e5cf860-e9c2-463a-972a-ed1c329d415b")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_documents()
    elif command in ["summary", "status", "analysis"]:
        if len(sys.argv) < 3:
            print(f"❌ 请提供文档ID")
            print(f"使用方法: python view_results.py {command} <document_id>")
            return
        
        document_id = sys.argv[2]
        
        if command == "summary":
            view_summary(document_id)
        elif command == "status":
            view_status(document_id)
        elif command == "analysis":
            view_analysis(document_id)
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令: list, summary, status, analysis")

if __name__ == "__main__":
    main()