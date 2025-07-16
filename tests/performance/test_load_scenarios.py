"""
负载测试场景
包括持续负载、峰值负载、并发操作等高级测试场景
"""

import asyncio
import time
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
import aiohttp
import matplotlib.pyplot as plt
from collections import deque
import numpy as np

from test_api_performance import APIPerformanceTester, BASE_URL, HEADERS


class LoadScenarioTester:
    """负载场景测试器"""
    
    def __init__(self, base_url: str, headers: Dict[str, str]):
        self.base_url = base_url
        self.headers = headers
        self.metrics_history = {
            "timestamps": deque(maxlen=1000),
            "response_times": deque(maxlen=1000),
            "throughput": deque(maxlen=100),
            "error_rates": deque(maxlen=100),
            "active_requests": deque(maxlen=1000)
        }
    
    async def sustained_load_test(
        self,
        duration_seconds: int = 300,  # 5分钟
        requests_per_second: int = 10
    ):
        """持续负载测试"""
        print(f"\n开始持续负载测试")
        print(f"持续时间: {duration_seconds}秒")
        print(f"目标RPS: {requests_per_second}")
        print("-" * 60)
        
        start_time = time.time()
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                batch_start = time.time()
                
                # 创建一批请求
                tasks = []
                for _ in range(requests_per_second):
                    task = self._make_monitored_request(
                        session,
                        "GET",
                        f"{self.base_url}/projects"
                    )
                    tasks.append(task)
                
                # 执行请求
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 统计结果
                for result in results:
                    if isinstance(result, dict):
                        total_requests += 1
                        if result.get("success"):
                            successful_requests += 1
                            response_times.append(result["time"])
                        else:
                            failed_requests += 1
                    else:
                        failed_requests += 1
                        total_requests += 1
                
                # 更新指标
                current_time = time.time() - start_time
                self._update_metrics(
                    timestamp=current_time,
                    response_times=response_times[-requests_per_second:],
                    success_count=successful_requests,
                    total_count=total_requests
                )
                
                # 显示进度
                elapsed = time.time() - start_time
                current_rps = total_requests / elapsed if elapsed > 0 else 0
                print(f"\r时间: {elapsed:.0f}s | 请求: {total_requests} | "
                      f"RPS: {current_rps:.1f} | 成功率: "
                      f"{(successful_requests/total_requests*100 if total_requests > 0 else 0):.1f}%", 
                      end="")
                
                # 等待到下一秒
                batch_duration = time.time() - batch_start
                if batch_duration < 1.0:
                    await asyncio.sleep(1.0 - batch_duration)
        
        # 生成报告
        self._generate_sustained_load_report(
            duration=time.time() - start_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            response_times=response_times
        )
    
    async def spike_load_test(
        self,
        normal_rps: int = 10,
        spike_rps: int = 100,
        normal_duration: int = 60,
        spike_duration: int = 30
    ):
        """峰值负载测试"""
        print(f"\n开始峰值负载测试")
        print(f"正常负载: {normal_rps} RPS，持续 {normal_duration}秒")
        print(f"峰值负载: {spike_rps} RPS，持续 {spike_duration}秒")
        print("-" * 60)
        
        phases = [
            ("预热阶段", normal_rps, normal_duration),
            ("峰值阶段", spike_rps, spike_duration),
            ("恢复阶段", normal_rps, normal_duration)
        ]
        
        overall_results = []
        
        for phase_name, rps, duration in phases:
            print(f"\n\n{phase_name}:")
            phase_results = await self._execute_load_phase(rps, duration)
            overall_results.append({
                "phase": phase_name,
                "results": phase_results
            })
        
        # 生成峰值测试报告
        self._generate_spike_test_report(overall_results)
    
    async def step_load_test(
        self,
        initial_rps: int = 5,
        step_size: int = 5,
        step_duration: int = 60,
        max_rps: int = 50
    ):
        """阶梯负载测试"""
        print(f"\n开始阶梯负载测试")
        print(f"初始RPS: {initial_rps}")
        print(f"步长: {step_size} RPS")
        print(f"每步持续: {step_duration}秒")
        print(f"最大RPS: {max_rps}")
        print("-" * 60)
        
        current_rps = initial_rps
        step_results = []
        
        while current_rps <= max_rps:
            print(f"\n当前负载: {current_rps} RPS")
            
            results = await self._execute_load_phase(current_rps, step_duration)
            
            # 检查系统是否还能承受
            error_rate = results["failed"] / results["total"] if results["total"] > 0 else 0
            avg_response_time = np.mean(results["response_times"]) if results["response_times"] else 0
            
            step_results.append({
                "rps": current_rps,
                "results": results,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time
            })
            
            # 如果错误率过高或响应时间过长，停止测试
            if error_rate > 0.1 or avg_response_time > 5.0:
                print(f"\n系统达到性能瓶颈:")
                print(f"  错误率: {error_rate:.2%}")
                print(f"  平均响应时间: {avg_response_time:.2f}秒")
                break
            
            current_rps += step_size
        
        # 生成阶梯测试报告
        self._generate_step_test_report(step_results)
    
    async def mixed_workload_test(
        self,
        duration_seconds: int = 180,
        concurrent_users: int = 50
    ):
        """混合工作负载测试"""
        print(f"\n开始混合工作负载测试")
        print(f"模拟用户数: {concurrent_users}")
        print(f"持续时间: {duration_seconds}秒")
        print("-" * 60)
        
        # 定义用户行为模式
        user_behaviors = [
            self._browse_projects_behavior,
            self._create_and_manage_project_behavior,
            self._document_upload_behavior,
            self._cognitive_chat_behavior
        ]
        
        # 创建虚拟用户
        users = []
        for i in range(concurrent_users):
            behavior = random.choice(user_behaviors)
            user_task = asyncio.create_task(
                self._simulate_user(f"user_{i}", behavior, duration_seconds)
            )
            users.append(user_task)
        
        # 等待所有用户完成
        results = await asyncio.gather(*users)
        
        # 生成混合负载报告
        self._generate_mixed_load_report(results)
    
    async def _execute_load_phase(self, rps: int, duration: int) -> Dict[str, Any]:
        """执行负载阶段"""
        start_time = time.time()
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                batch_start = time.time()
                
                # 创建请求
                tasks = []
                for _ in range(rps):
                    task = self._make_monitored_request(
                        session,
                        "GET",
                        f"{self.base_url}/projects"
                    )
                    tasks.append(task)
                
                # 执行请求
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 统计结果
                for result in results:
                    if isinstance(result, dict):
                        total_requests += 1
                        if result.get("success"):
                            successful_requests += 1
                            response_times.append(result["time"])
                        else:
                            failed_requests += 1
                
                # 等待到下一秒
                batch_duration = time.time() - batch_start
                if batch_duration < 1.0:
                    await asyncio.sleep(1.0 - batch_duration)
        
        return {
            "total": total_requests,
            "successful": successful_requests,
            "failed": failed_requests,
            "response_times": response_times,
            "duration": time.time() - start_time
        }
    
    async def _make_monitored_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """执行受监控的请求"""
        start_time = time.time()
        try:
            async with session.request(
                method,
                url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30),
                **kwargs
            ) as response:
                await response.text()
                end_time = time.time()
                return {
                    "success": response.status < 400,
                    "status": response.status,
                    "time": end_time - start_time
                }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "timeout",
                "time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time": time.time() - start_time
            }
    
    def _update_metrics(
        self,
        timestamp: float,
        response_times: List[float],
        success_count: int,
        total_count: int
    ):
        """更新性能指标"""
        self.metrics_history["timestamps"].append(timestamp)
        
        if response_times:
            avg_response_time = np.mean(response_times)
            self.metrics_history["response_times"].append(avg_response_time)
        
        if total_count > 0:
            error_rate = 1.0 - (success_count / total_count)
            self.metrics_history["error_rates"].append(error_rate)
    
    async def _simulate_user(
        self,
        user_id: str,
        behavior_func,
        duration: int
    ) -> Dict[str, Any]:
        """模拟单个用户行为"""
        start_time = time.time()
        actions_performed = 0
        errors_encountered = 0
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                try:
                    await behavior_func(session, user_id)
                    actions_performed += 1
                except Exception as e:
                    errors_encountered += 1
                
                # 用户思考时间（1-5秒）
                await asyncio.sleep(random.uniform(1, 5))
        
        return {
            "user_id": user_id,
            "actions": actions_performed,
            "errors": errors_encountered,
            "duration": time.time() - start_time
        }
    
    async def _browse_projects_behavior(self, session: aiohttp.ClientSession, user_id: str):
        """浏览项目行为"""
        # 获取项目列表
        await self._make_monitored_request(session, "GET", f"{self.base_url}/projects")
        
        # 随机查看某个项目详情
        project_id = f"test-project-{random.randint(1, 100)}"
        await self._make_monitored_request(
            session,
            "GET",
            f"{self.base_url}/projects/{project_id}"
        )
    
    async def _create_and_manage_project_behavior(
        self,
        session: aiohttp.ClientSession,
        user_id: str
    ):
        """创建和管理项目行为"""
        # 创建项目
        project_data = {
            "name": f"用户{user_id}的项目-{int(time.time())}",
            "type": "research"
        }
        
        result = await self._make_monitored_request(
            session,
            "POST",
            f"{self.base_url}/projects",
            json=project_data
        )
        
        # 创建一些任务
        if result.get("success"):
            for i in range(random.randint(1, 3)):
                task_data = {
                    "title": f"任务 {i+1}",
                    "type": "data_collection"
                }
                await self._make_monitored_request(
                    session,
                    "POST",
                    f"{self.base_url}/projects/test-id/tasks",
                    json=task_data
                )
    
    async def _document_upload_behavior(self, session: aiohttp.ClientSession, user_id: str):
        """文档上传行为"""
        # 模拟文档上传（实际测试中应该使用真实文件）
        await self._make_monitored_request(
            session,
            "GET",
            f"{self.base_url}/documents"
        )
    
    async def _cognitive_chat_behavior(self, session: aiohttp.ClientSession, user_id: str):
        """认知对话行为"""
        questions = [
            "这个项目的主要目标是什么？",
            "有哪些相关的研究文献？",
            "请总结当前的进展"
        ]
        
        chat_data = {
            "message": random.choice(questions),
            "project_id": "test-project-id"
        }
        
        await self._make_monitored_request(
            session,
            "POST",
            f"{self.base_url}/cognitive/chat",
            json=chat_data
        )
    
    def _generate_sustained_load_report(self, **kwargs):
        """生成持续负载测试报告"""
        print("\n\n" + "="*60)
        print("持续负载测试报告")
        print("="*60)
        
        total = kwargs["total_requests"]
        successful = kwargs["successful_requests"]
        failed = kwargs["failed_requests"]
        response_times = kwargs["response_times"]
        duration = kwargs["duration"]
        
        print(f"测试持续时间: {duration:.1f}秒")
        print(f"总请求数: {total}")
        print(f"成功请求: {successful}")
        print(f"失败请求: {failed}")
        print(f"成功率: {(successful/total*100 if total > 0 else 0):.2f}%")
        print(f"平均RPS: {total/duration:.2f}")
        
        if response_times:
            print(f"\n响应时间统计:")
            print(f"  最小: {min(response_times):.3f}秒")
            print(f"  最大: {max(response_times):.3f}秒")
            print(f"  平均: {np.mean(response_times):.3f}秒")
            print(f"  P50: {np.percentile(response_times, 50):.3f}秒")
            print(f"  P95: {np.percentile(response_times, 95):.3f}秒")
            print(f"  P99: {np.percentile(response_times, 99):.3f}秒")
    
    def _generate_spike_test_report(self, results: List[Dict]):
        """生成峰值测试报告"""
        print("\n\n" + "="*60)
        print("峰值负载测试报告")
        print("="*60)
        
        for phase_result in results:
            phase = phase_result["phase"]
            data = phase_result["results"]
            
            print(f"\n{phase}:")
            print(f"  总请求: {data['total']}")
            print(f"  成功率: {(data['successful']/data['total']*100 if data['total'] > 0 else 0):.2f}%")
            
            if data['response_times']:
                print(f"  平均响应时间: {np.mean(data['response_times']):.3f}秒")
                print(f"  P95响应时间: {np.percentile(data['response_times'], 95):.3f}秒")
    
    def _generate_step_test_report(self, results: List[Dict]):
        """生成阶梯测试报告"""
        print("\n\n" + "="*60)
        print("阶梯负载测试报告")
        print("="*60)
        
        print("\nRPS | 错误率 | 平均响应时间 | P95响应时间")
        print("-" * 50)
        
        for step in results:
            rps = step["rps"]
            error_rate = step["error_rate"]
            avg_time = step["avg_response_time"]
            
            response_times = step["results"]["response_times"]
            p95_time = np.percentile(response_times, 95) if response_times else 0
            
            print(f"{rps:3d} | {error_rate:6.2%} | {avg_time:11.3f}s | {p95_time:10.3f}s")
        
        # 找出系统容量
        for i, step in enumerate(results):
            if step["error_rate"] > 0.05:  # 5%错误率阈值
                if i > 0:
                    print(f"\n系统建议容量: {results[i-1]['rps']} RPS")
                break
    
    def _generate_mixed_load_report(self, results: List[Dict]):
        """生成混合负载测试报告"""
        print("\n\n" + "="*60)
        print("混合工作负载测试报告")
        print("="*60)
        
        total_actions = sum(r["actions"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        
        print(f"模拟用户数: {len(results)}")
        print(f"总操作数: {total_actions}")
        print(f"总错误数: {total_errors}")
        print(f"错误率: {(total_errors/total_actions*100 if total_actions > 0 else 0):.2f}%")
        
        # 计算每用户平均操作数
        avg_actions = total_actions / len(results) if results else 0
        print(f"每用户平均操作数: {avg_actions:.1f}")


async def run_load_tests():
    """运行所有负载测试"""
    tester = LoadScenarioTester(BASE_URL, HEADERS)
    
    # 1. 持续负载测试
    await tester.sustained_load_test(
        duration_seconds=60,  # 简化为1分钟用于演示
        requests_per_second=20
    )
    
    # 2. 峰值负载测试
    await tester.spike_load_test(
        normal_rps=10,
        spike_rps=50,
        normal_duration=30,
        spike_duration=15
    )
    
    # 3. 阶梯负载测试
    await tester.step_load_test(
        initial_rps=5,
        step_size=5,
        step_duration=30,
        max_rps=30
    )
    
    # 4. 混合工作负载测试
    await tester.mixed_workload_test(
        duration_seconds=60,
        concurrent_users=20
    )


if __name__ == "__main__":
    print("DPA 高级负载测试")
    print("=" * 60)
    
    asyncio.run(run_load_tests())