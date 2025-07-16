"""
系统稳定性测试
验证所有修复后的功能是否正常工作
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
import json
from typing import Dict, List, Any
import aiohttp

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# API基础URL
BASE_URL = "http://localhost:8200"
HEADERS = {"X-USER-ID": "u1", "Content-Type": "application/json"}


async def test_health_check(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """测试健康检查"""
    try:
        async with session.get(f"{BASE_URL}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "endpoint": "/health",
                    "status": "success",
                    "response_time": 0.1,
                    "services": data.get("services", {})
                }
            else:
                return {
                    "endpoint": "/health",
                    "status": "failed",
                    "error": f"HTTP {resp.status}"
                }
    except Exception as e:
        return {
            "endpoint": "/health",
            "status": "error",
            "error": str(e)
        }


async def test_aag_skim(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """测试AAG略读功能"""
    start_time = time.time()
    
    payload = {
        "document_id": "aa0e56f0-8234-4b02-bd49-c00ddcc08c1f",
        "document_content": "人工智能是计算机科学的一个重要分支，致力于创建能够模拟人类智能的系统。"
    }
    
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/aag/skim",
            json=payload,
            headers=HEADERS
        ) as resp:
            duration = time.time() - start_time
            
            if resp.status == 200:
                data = await resp.json()
                return {
                    "endpoint": "AAG略读",
                    "status": "success",
                    "response_time": duration,
                    "has_result": bool(data.get("result"))
                }
            else:
                return {
                    "endpoint": "AAG略读",
                    "status": "failed",
                    "response_time": duration,
                    "error": f"HTTP {resp.status}"
                }
    except Exception as e:
        return {
            "endpoint": "AAG略读",
            "status": "error",
            "error": str(e)
        }


async def test_ultra_fast_qa(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """测试超快速问答"""
    questions = [
        "什么是人工智能？",
        "什么是机器学习？",
        "量子计算的原理是什么？"
    ]
    
    results = []
    
    for question in questions:
        start_time = time.time()
        
        payload = {"question": question}
        
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/qa/ultra-fast/answer",
                json=payload,
                headers=HEADERS
            ) as resp:
                duration = time.time() - start_time
                
                if resp.status == 200:
                    data = await resp.json()
                    results.append({
                        "question": question[:20] + "...",
                        "status": "success",
                        "response_time": duration,
                        "mode": data.get("mode", "unknown")
                    })
                else:
                    results.append({
                        "question": question[:20] + "...",
                        "status": "failed",
                        "response_time": duration,
                        "error": f"HTTP {resp.status}"
                    })
        except Exception as e:
            results.append({
                "question": question[:20] + "...",
                "status": "error",
                "error": str(e)
            })
    
    # 计算平均响应时间
    success_times = [r["response_time"] for r in results if r["status"] == "success"]
    avg_time = sum(success_times) / len(success_times) if success_times else 0
    
    return {
        "endpoint": "超快速问答",
        "status": "success" if avg_time > 0 else "failed",
        "average_response_time": avg_time,
        "target_met": avg_time < 1.0 if avg_time > 0 else False,
        "details": results
    }


async def test_mvp_qa(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """测试MVP问答系统"""
    start_time = time.time()
    
    payload = {
        "question": "深度学习的应用有哪些？",
        "top_k": 5,
        "include_memory": False
    }
    
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/qa/mvp/answer",
            json=payload,
            headers=HEADERS
        ) as resp:
            duration = time.time() - start_time
            
            if resp.status == 200:
                data = await resp.json()
                return {
                    "endpoint": "MVP问答",
                    "status": "success",
                    "response_time": duration,
                    "has_answer": bool(data.get("answer")),
                    "context_count": len(data.get("context_used", []))
                }
            else:
                return {
                    "endpoint": "MVP问答",
                    "status": "failed",
                    "response_time": duration,
                    "error": f"HTTP {resp.status}"
                }
    except Exception as e:
        return {
            "endpoint": "MVP问答",
            "status": "error",
            "error": str(e)
        }


async def test_database_connections(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """测试数据库连接状态"""
    try:
        async with session.get(f"{BASE_URL}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                services = data.get("services", {})
                
                return {
                    "endpoint": "数据库连接",
                    "status": "success" if data.get("status") == "healthy" else "degraded",
                    "postgresql": services.get("postgresql", "unknown"),
                    "qdrant": services.get("qdrant", "unknown"),
                    "neo4j": services.get("neo4j", "unknown")
                }
            else:
                return {
                    "endpoint": "数据库连接",
                    "status": "failed",
                    "error": f"HTTP {resp.status}"
                }
    except Exception as e:
        return {
            "endpoint": "数据库连接",
            "status": "error",
            "error": str(e)
        }


async def run_stability_tests():
    """运行所有稳定性测试"""
    print("="*60)
    print("系统稳定性测试")
    print("="*60)
    
    # 创建HTTP会话
    async with aiohttp.ClientSession() as session:
        # 1. 健康检查
        print("\n1. 测试健康检查...")
        health_result = await test_health_check(session)
        print(f"   状态: {health_result['status']}")
        if health_result.get('services'):
            for service, status in health_result['services'].items():
                print(f"   - {service}: {status}")
        
        # 2. 数据库连接
        print("\n2. 测试数据库连接...")
        db_result = await test_database_connections(session)
        print(f"   状态: {db_result['status']}")
        print(f"   - PostgreSQL: {db_result.get('postgresql', 'unknown')}")
        print(f"   - Qdrant: {db_result.get('qdrant', 'unknown')}")
        print(f"   - Neo4j: {db_result.get('neo4j', 'unknown')}")
        
        # 3. AAG功能
        print("\n3. 测试AAG略读功能...")
        aag_result = await test_aag_skim(session)
        print(f"   状态: {aag_result['status']}")
        if aag_result['status'] == 'success':
            print(f"   响应时间: {aag_result['response_time']:.3f}秒")
        
        # 4. 超快速问答
        print("\n4. 测试超快速问答...")
        fast_qa_result = await test_ultra_fast_qa(session)
        print(f"   状态: {fast_qa_result['status']}")
        if fast_qa_result['status'] == 'success':
            print(f"   平均响应时间: {fast_qa_result['average_response_time']:.3f}秒")
            print(f"   目标达成(<1秒): {'✅' if fast_qa_result['target_met'] else '❌'}")
            for detail in fast_qa_result['details']:
                print(f"   - {detail['question']}: {detail['response_time']:.3f}秒 ({detail.get('mode', 'N/A')})")
        
        # 5. MVP问答
        print("\n5. 测试MVP问答系统...")
        mvp_result = await test_mvp_qa(session)
        print(f"   状态: {mvp_result['status']}")
        if mvp_result['status'] == 'success':
            print(f"   响应时间: {mvp_result['response_time']:.3f}秒")
            print(f"   上下文数量: {mvp_result.get('context_count', 0)}")
        
        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        
        all_results = [health_result, db_result, aag_result, fast_qa_result, mvp_result]
        success_count = sum(1 for r in all_results if r['status'] == 'success')
        total_count = len(all_results)
        
        print(f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        # 性能指标
        if fast_qa_result['status'] == 'success':
            print(f"\n性能指标:")
            print(f"- 超快速问答平均响应: {fast_qa_result['average_response_time']:.3f}秒")
            if mvp_result['status'] == 'success':
                print(f"- MVP问答响应: {mvp_result['response_time']:.3f}秒")
        
        # 问题汇总
        problems = []
        for result in all_results:
            if result['status'] != 'success':
                problems.append(f"- {result['endpoint']}: {result.get('error', 'Failed')}")
        
        if problems:
            print(f"\n发现的问题:")
            for problem in problems:
                print(problem)
        else:
            print(f"\n✅ 所有系统功能正常运行！")
        
        return {
            "success_rate": success_count / total_count,
            "all_passed": success_count == total_count,
            "results": all_results
        }


if __name__ == "__main__":
    asyncio.run(run_stability_tests())