#!/usr/bin/env python3
"""
测试V3认知系统API桥接层
验证API端点的可用性和功能
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "http://localhost:8001/api/v1"

async def test_cognitive_api():
    """测试认知系统API"""
    
    async with aiohttp.ClientSession() as session:
        
        print("🧠 测试DPA V3认知系统API桥接层")
        print("=" * 50)
        
        # 1. 测试健康检查
        print("\n1. 测试认知系统健康检查...")
        try:
            async with session.get(f"{API_BASE}/cognitive/health") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ 健康检查通过: {result['status']}")
                    print(f"   组件状态: {result['components']}")
                else:
                    print(f"❌ 健康检查失败: {resp.status}")
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
        
        # 2. 测试认知分析
        print("\n2. 测试认知分析功能...")
        try:
            analysis_data = {
                "document_text": "这是一个关于人工智能和机器学习的测试文档。文档包含了深度学习、神经网络、自然语言处理等关键概念。这些技术正在改变我们对智能系统的理解。",
                "project_id": "test_project",
                "analysis_type": "comprehensive",
                "analysis_goal": "理解AI技术的核心概念",
                "use_memory": True,
                "enable_metacognition": True
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-USER-ID": "test_user"
            }
            
            async with session.post(
                f"{API_BASE}/cognitive/analyze",
                json=analysis_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ 认知分析成功")
                    print(f"   分析ID: {result['analysis_id']}")
                    print(f"   分块数量: {result['chunks_created']}")
                    print(f"   检索结果: {result['retrieval_results']}")
                    print(f"   认知策略: {result['metacognitive_strategy']}")
                    print(f"   性能评分: {result['performance_score']:.3f}")
                    print(f"   置信水平: {result['confidence_level']}")
                    print(f"   洞察数量: {len(result['insights'])}")
                    
                    # 保存认知状态ID用于后续测试
                    cognitive_state_id = result['cognitive_state_id']
                    
                else:
                    error_text = await resp.text()
                    print(f"❌ 认知分析失败: {resp.status}")
                    print(f"   错误信息: {error_text}")
                    return
                    
        except Exception as e:
            print(f"❌ 认知分析异常: {e}")
            return
        
        # 3. 测试认知对话
        print("\n3. 测试认知对话功能...")
        try:
            chat_data = {
                "message": "请解释一下深度学习和机器学习的区别",
                "project_id": "test_project",
                "use_memory": True,
                "strategy": "exploration",
                "max_results": 10
            }
            
            async with session.post(
                f"{API_BASE}/cognitive/chat",
                json=chat_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ 认知对话成功")
                    print(f"   对话ID: {result['conversation_id']}")
                    print(f"   使用策略: {result['strategy_used']}")
                    print(f"   置信评分: {result['confidence_score']:.3f}")
                    print(f"   信息源数量: {len(result['sources'])}")
                    print(f"   处理时间: {result['processing_time']:.3f}s")
                    print(f"   响应预览: {result['response'][:200]}...")
                    
                else:
                    error_text = await resp.text()
                    print(f"❌ 认知对话失败: {resp.status}")
                    print(f"   错误信息: {error_text}")
                    
        except Exception as e:
            print(f"❌ 认知对话异常: {e}")
        
        # 4. 测试记忆库查询
        print("\n4. 测试记忆库查询...")
        try:
            memory_data = {
                "query": "人工智能相关概念",
                "project_id": "test_project",
                "memory_types": ["all"],
                "limit": 10
            }
            
            async with session.post(
                f"{API_BASE}/cognitive/memory/query",
                json=memory_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ 记忆库查询成功")
                    print(f"   查询结果数量: {len(result['results'])}")
                    print(f"   搜索策略: {result['search_strategy']}")
                    print(f"   记忆统计: {result['memory_stats']}")
                    
                else:
                    error_text = await resp.text()
                    print(f"❌ 记忆库查询失败: {resp.status}")
                    print(f"   错误信息: {error_text}")
                    
        except Exception as e:
            print(f"❌ 记忆库查询异常: {e}")
        
        # 5. 测试认知状态查询
        print("\n5. 测试认知状态查询...")
        try:
            if 'cognitive_state_id' in locals():
                async with session.get(
                    f"{API_BASE}/cognitive/state/{cognitive_state_id}",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"✅ 认知状态查询成功")
                        print(f"   线程ID: {result['thread_id']}")
                        print(f"   工作记忆项数: {len(result['working_memory'])}")
                        print(f"   情节记忆数量: {len(result['episodic_memory'])}")
                        print(f"   语义记忆数量: {len(result['semantic_memory'])}")
                        print(f"   处理状态: {result['processing_status']}")
                        
                    else:
                        error_text = await resp.text()
                        print(f"❌ 认知状态查询失败: {resp.status}")
                        print(f"   错误信息: {error_text}")
            else:
                print("⚠️  跳过认知状态查询（没有有效的状态ID）")
                    
        except Exception as e:
            print(f"❌ 认知状态查询异常: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 V3认知系统API测试完成")


async def test_performance():
    """测试API性能"""
    print("\n📊 测试API性能...")
    
    async with aiohttp.ClientSession() as session:
        headers = {"X-USER-ID": "test_user"}
        
        # 并发测试
        start_time = datetime.now()
        
        tasks = []
        for i in range(5):
            chat_data = {
                "message": f"测试并发请求 #{i+1}",
                "project_id": "performance_test",
                "use_memory": False,  # 减少处理时间
                "max_results": 5
            }
            
            task = session.post(
                f"{API_BASE}/cognitive/chat",
                json=chat_data,
                headers=headers
            )
            tasks.append(task)
        
        # 执行并发请求
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        successful_requests = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
        
        print(f"   并发请求数: 5")
        print(f"   成功请求数: {successful_requests}")
        print(f"   总耗时: {total_time:.3f}s")
        print(f"   平均耗时: {total_time/5:.3f}s")
        
        # 关闭所有响应
        for resp in responses:
            if hasattr(resp, 'close'):
                resp.close()


if __name__ == "__main__":
    print("启动认知系统API测试...")
    print("请确保API服务器正在运行在 http://localhost:8001 (dpa_gen环境)")
    print("前端服务器运行在 http://localhost:8031")
    print()
    
    try:
        # 运行主要测试
        asyncio.run(test_cognitive_api())
        
        # 运行性能测试
        asyncio.run(test_performance())
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()