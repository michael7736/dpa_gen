#!/usr/bin/env python3
"""
检查MinIO中的分析结果
"""

import asyncio
import json
from src.services.minio_service import get_minio_service

DOCUMENT_ID = "5ec3e004-ab9c-40af-9ed3-0837fddfc628"
PROJECT_ID = "e1900ad1-f1a1-4e80-8796-9c45c7e124a5"
USER_ID = "243588ff-459d-45b8-b77b-09aec3946a64"

async def check_analysis_result():
    minio_service = get_minio_service()
    
    try:
        # 获取分析结果
        print("1. 获取分析结果...")
        result = await minio_service.get_processing_result(
            user_id=USER_ID,
            project_id=PROJECT_ID,
            document_id=DOCUMENT_ID,
            result_type="analysis"
        )
        
        if result:
            print("✅ 找到分析结果")
            
            # 打印基本信息
            print(f"\n基本信息:")
            print(f"  成功: {result.get('success')}")
            print(f"  分析ID: {result.get('analysis_id')}")
            print(f"  分析深度: {result.get('analysis_depth')}")
            print(f"  错误: {result.get('error')}")
            
            # 打印结果概要
            if result.get('result'):
                res = result['result']
                print(f"\n结果概要:")
                print(f"  执行摘要长度: {len(res.get('executive_summary', ''))}")
                print(f"  关键洞察数: {len(res.get('key_insights', []))}")
                print(f"  行动项数: {len(res.get('action_items', []))}")
                print(f"  可视化数据: {bool(res.get('visualization_data'))}")
                
                # 打印部分内容
                if res.get('executive_summary'):
                    print(f"\n执行摘要（前200字）:")
                    print(res['executive_summary'][:200] + "...")
                    
                if res.get('key_insights'):
                    print(f"\n前3个关键洞察:")
                    for i, insight in enumerate(res['key_insights'][:3], 1):
                        print(f"  {i}. {insight}")
                        
                if res.get('action_items'):
                    print(f"\n前3个行动项:")
                    for i, item in enumerate(res['action_items'][:3], 1):
                        print(f"  {i}. {item}")
                        
                # 保存完整结果到文件
                with open('analysis_result_full.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n完整结果已保存到: analysis_result_full.json")
            else:
                print("\n⚠️ 结果为空")
                
        else:
            print("❌ 没有找到分析结果")
            
        # 检查其他结果
        print("\n2. 检查其他处理结果...")
        for result_type in ['summary', 'index']:
            try:
                other_result = await minio_service.get_processing_result(
                    user_id=USER_ID,
                    project_id=PROJECT_ID,
                    document_id=DOCUMENT_ID,
                    result_type=result_type
                )
                if other_result:
                    print(f"  ✅ {result_type}: 存在")
                else:
                    print(f"  ❌ {result_type}: 不存在")
            except Exception as e:
                print(f"  ❌ {result_type}: 错误 - {e}")
                
    except Exception as e:
        print(f"❌ 错误: {e}")

async def main():
    print("🔍 分析结果检查")
    print("=" * 50)
    print(f"文档ID: {DOCUMENT_ID}")
    await check_analysis_result()

if __name__ == "__main__":
    asyncio.run(main())