"""
最终集成测试
全面验证系统所有功能的集成情况
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
import aiohttp
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"
DEFAULT_PROJECT_ID = "p1"
DEFAULT_DOCUMENT_ID = "aa0e56f0-8234-4b02-bd49-c00ddcc08c1f"


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.start_time = time.time()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    def add_result(self, category: str, test_name: str, status: str, 
                   details: Optional[Dict] = None, error: Optional[str] = None):
        """添加测试结果"""
        self.results.append({
            "category": category,
            "test_name": test_name,
            "status": status,
            "details": details or {},
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_health_and_connectivity(self):
        """测试1: 健康检查和连通性"""
        print("\n1. 测试健康检查和连通性...")
        
        # 1.1 基础健康检查
        try:
            async with self.session.get(f"{BASE_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.add_result("连通性", "健康检查", "success", {
                        "status": data.get("status"),
                        "services": data.get("services", {})
                    })
                    print("   ✅ 健康检查通过")
                else:
                    self.add_result("连通性", "健康检查", "failed", 
                                  error=f"HTTP {resp.status}")
                    print(f"   ❌ 健康检查失败: HTTP {resp.status}")
        except Exception as e:
            self.add_result("连通性", "健康检查", "error", error=str(e))
            print(f"   ❌ 健康检查错误: {e}")
            
        # 1.2 API文档
        try:
            async with self.session.get(f"{BASE_URL}/docs") as resp:
                self.add_result("连通性", "API文档", 
                              "success" if resp.status == 200 else "failed")
                print(f"   {'✅' if resp.status == 200 else '❌'} API文档访问")
        except Exception as e:
            self.add_result("连通性", "API文档", "error", error=str(e))
            
    async def test_aag_functions(self):
        """测试2: AAG分析功能"""
        print("\n2. 测试AAG分析功能...")
        
        headers = {
            "X-USER-ID": USER_ID,
            "Content-Type": "application/json"
        }
        
        # 2.1 略读功能
        payload = {
            "document_id": DEFAULT_DOCUMENT_ID,
            "document_content": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
        }
        
        try:
            start = time.time()
            async with self.session.post(
                f"{BASE_URL}/api/v1/aag/skim",
                json=payload,
                headers=headers
            ) as resp:
                duration = time.time() - start
                
                if resp.status == 200:
                    data = await resp.json()
                    self.add_result("AAG", "略读分析", "success", {
                        "response_time": duration,
                        "has_result": bool(data.get("result"))
                    })
                    print(f"   ✅ 略读分析成功 ({duration:.2f}秒)")
                else:
                    text = await resp.text()
                    self.add_result("AAG", "略读分析", "failed", 
                                  error=f"HTTP {resp.status}: {text}")
                    print(f"   ❌ 略读分析失败: HTTP {resp.status}")
        except Exception as e:
            self.add_result("AAG", "略读分析", "error", error=str(e))
            print(f"   ❌ 略读分析错误: {e}")
            
    async def test_qa_performance(self):
        """测试3: 问答系统性能"""
        print("\n3. 测试问答系统性能...")
        
        headers = {
            "X-USER-ID": USER_ID,
            "Content-Type": "application/json"
        }
        
        # 3.1 超快速问答
        questions = [
            "什么是人工智能？",
            "什么是机器学习？",
            "深度学习有什么应用？"
        ]
        
        fast_qa_times = []
        for question in questions:
            try:
                start = time.time()
                async with self.session.post(
                    f"{BASE_URL}/api/v1/qa/ultra-fast/answer",
                    json={"question": question},
                    headers=headers
                ) as resp:
                    duration = time.time() - start
                    
                    if resp.status == 200:
                        data = await resp.json()
                        fast_qa_times.append(duration)
                        mode = data.get("mode", "unknown")
                        print(f"   ✅ 超快速问答: {question[:20]}... ({duration:.3f}秒, {mode}模式)")
                    else:
                        print(f"   ❌ 超快速问答失败: {question[:20]}...")
            except Exception as e:
                print(f"   ❌ 超快速问答错误: {e}")
                
        if fast_qa_times:
            avg_time = sum(fast_qa_times) / len(fast_qa_times)
            self.add_result("问答性能", "超快速问答", "success", {
                "average_time": avg_time,
                "target_met": avg_time < 1.0,
                "test_count": len(fast_qa_times)
            })
            print(f"   📊 平均响应时间: {avg_time:.3f}秒 ({'✅ 达标' if avg_time < 1.0 else '❌ 未达标'})")
            
        # 3.2 MVP问答系统
        try:
            start = time.time()
            async with self.session.post(
                f"{BASE_URL}/api/v1/qa/mvp/answer",
                json={
                    "question": "什么是自然语言处理？",
                    "top_k": 5,
                    "include_memory": False
                },
                headers=headers
            ) as resp:
                duration = time.time() - start
                
                if resp.status == 200:
                    data = await resp.json()
                    self.add_result("问答性能", "MVP问答", "success", {
                        "response_time": duration,
                        "context_count": len(data.get("context_used", []))
                    })
                    print(f"   ✅ MVP问答成功 ({duration:.2f}秒)")
                else:
                    self.add_result("问答性能", "MVP问答", "failed")
                    print(f"   ❌ MVP问答失败")
        except Exception as e:
            self.add_result("问答性能", "MVP问答", "error", error=str(e))
            print(f"   ❌ MVP问答错误: {e}")
            
        # 3.3 简化问答接口
        try:
            start = time.time()
            async with self.session.post(
                f"{BASE_URL}/api/v1/qa/answer-simple",
                json={"question": "什么是神经网络？"},
                headers=headers
            ) as resp:
                duration = time.time() - start
                
                if resp.status == 200:
                    self.add_result("问答性能", "简化问答", "success", {
                        "response_time": duration
                    })
                    print(f"   ✅ 简化问答成功 ({duration:.2f}秒)")
                else:
                    self.add_result("问答性能", "简化问答", "failed")
                    print(f"   ❌ 简化问答失败")
        except Exception as e:
            self.add_result("问答性能", "简化问答", "error", error=str(e))
            
    async def test_document_operations(self):
        """测试4: 文档操作"""
        print("\n4. 测试文档操作...")
        
        headers = {
            "X-USER-ID": USER_ID,
            "Content-Type": "application/json"
        }
        
        # 4.1 获取文档列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/v1/documents",
                headers=headers,
                params={"project_id": DEFAULT_PROJECT_ID}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    doc_count = len(data) if isinstance(data, list) else data.get("total", 0)
                    self.add_result("文档操作", "获取文档列表", "success", {
                        "document_count": doc_count
                    })
                    print(f"   ✅ 获取文档列表成功 (共{doc_count}个文档)")
                else:
                    self.add_result("文档操作", "获取文档列表", "failed")
                    print(f"   ❌ 获取文档列表失败")
        except Exception as e:
            self.add_result("文档操作", "获取文档列表", "error", error=str(e))
            print(f"   ❌ 获取文档列表错误: {e}")
            
    async def test_project_operations(self):
        """测试5: 项目操作"""
        print("\n5. 测试项目操作...")
        
        headers = {
            "X-USER-ID": USER_ID,
            "Content-Type": "application/json"
        }
        
        # 5.1 获取项目列表
        try:
            async with self.session.get(
                f"{BASE_URL}/api/v1/projects",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    project_count = len(data) if isinstance(data, list) else 0
                    self.add_result("项目操作", "获取项目列表", "success", {
                        "project_count": project_count
                    })
                    print(f"   ✅ 获取项目列表成功 (共{project_count}个项目)")
                else:
                    self.add_result("项目操作", "获取项目列表", "failed")
                    print(f"   ❌ 获取项目列表失败")
        except Exception as e:
            self.add_result("项目操作", "获取项目列表", "error", error=str(e))
            print(f"   ❌ 获取项目列表错误: {e}")
            
    async def test_database_operations(self):
        """测试6: 数据库操作"""
        print("\n6. 测试数据库操作...")
        
        # 通过健康检查获取数据库状态
        try:
            async with self.session.get(f"{BASE_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    services = data.get("services", {})
                    
                    # 检查各个数据库
                    for db_name in ["qdrant", "neo4j"]:
                        status = services.get(db_name, "unknown")
                        self.add_result("数据库", f"{db_name}连接", 
                                      "success" if status == "healthy" else "failed",
                                      {"status": status})
                        print(f"   {'✅' if status == 'healthy' else '❌'} {db_name}: {status}")
        except Exception as e:
            self.add_result("数据库", "数据库检查", "error", error=str(e))
            print(f"   ❌ 数据库检查错误: {e}")
            
    def generate_report(self):
        """生成测试报告"""
        total_time = time.time() - self.start_time
        
        # 统计结果
        total_tests = len(self.results)
        success_count = sum(1 for r in self.results if r["status"] == "success")
        failed_count = sum(1 for r in self.results if r["status"] == "failed")
        error_count = sum(1 for r in self.results if r["status"] == "error")
        
        # 按类别分组
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"success": 0, "failed": 0, "error": 0}
            categories[cat][result["status"]] += 1
            
        print("\n" + "="*60)
        print("集成测试报告")
        print("="*60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"\n测试结果汇总:")
        print(f"  总测试数: {total_tests}")
        print(f"  ✅ 成功: {success_count} ({success_count/total_tests*100:.1f}%)")
        print(f"  ❌ 失败: {failed_count} ({failed_count/total_tests*100:.1f}%)")
        print(f"  ⚠️  错误: {error_count} ({error_count/total_tests*100:.1f}%)")
        
        print(f"\n分类结果:")
        for cat, stats in categories.items():
            total = sum(stats.values())
            success_rate = stats["success"] / total * 100 if total > 0 else 0
            print(f"  {cat}: {stats['success']}/{total} ({success_rate:.1f}%)")
            
        # 性能指标
        print(f"\n性能指标:")
        qa_results = [r for r in self.results if r["category"] == "问答性能" and r["status"] == "success"]
        for result in qa_results:
            if "average_time" in result["details"]:
                print(f"  - {result['test_name']}: 平均{result['details']['average_time']:.3f}秒")
            elif "response_time" in result["details"]:
                print(f"  - {result['test_name']}: {result['details']['response_time']:.3f}秒")
                
        # 问题列表
        problems = [r for r in self.results if r["status"] in ["failed", "error"]]
        if problems:
            print(f"\n发现的问题:")
            for problem in problems:
                print(f"  - [{problem['category']}] {problem['test_name']}: {problem.get('error', 'Failed')}")
        else:
            print(f"\n✅ 所有测试通过！")
            
        # 保存详细报告
        report = {
            "test_time": datetime.now().isoformat(),
            "total_duration": total_time,
            "summary": {
                "total": total_tests,
                "success": success_count,
                "failed": failed_count,
                "error": error_count,
                "success_rate": success_count / total_tests * 100 if total_tests > 0 else 0
            },
            "categories": categories,
            "details": self.results
        }
        
        with open("integration_test_results.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n详细报告已保存到: integration_test_results.json")
        
        return success_count == total_tests


async def run_integration_tests():
    """运行所有集成测试"""
    print("开始集成测试...")
    print("="*60)
    
    async with IntegrationTester() as tester:
        # 运行所有测试
        await tester.test_health_and_connectivity()
        await tester.test_aag_functions()
        await tester.test_qa_performance()
        await tester.test_document_operations()
        await tester.test_project_operations()
        await tester.test_database_operations()
        
        # 生成报告
        all_passed = tester.generate_report()
        
        return all_passed


if __name__ == "__main__":
    all_passed = asyncio.run(run_integration_tests())
    sys.exit(0 if all_passed else 1)