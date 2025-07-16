"""
API性能测试套件
包括响应时间、吞吐量、并发处理能力等测试
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import aiohttp
import json
import os
from dataclasses import dataclass

# 测试配置
BASE_URL = os.getenv("DPA_API_URL", "http://localhost:8001/api/v1")
TEST_TOKEN = os.getenv("DPA_TEST_TOKEN", "test-token")
HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


@dataclass
class PerformanceResult:
    """性能测试结果"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    min_time: float
    max_time: float
    mean_time: float
    median_time: float
    p95_time: float
    p99_time: float
    throughput: float  # 请求/秒
    error_rate: float
    timestamp: datetime


class APIPerformanceTester:
    """API性能测试器"""
    
    def __init__(self, base_url: str, headers: Dict[str, str]):
        self.base_url = base_url
        self.headers = headers
        self.results = []
    
    async def _make_request(self, session: aiohttp.ClientSession, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """执行单个请求并记录时间"""
        start_time = time.time()
        try:
            async with session.request(method, url, headers=self.headers, **kwargs) as response:
                await response.text()  # 确保读取完整响应
                end_time = time.time()
                return {
                    "success": response.status < 400,
                    "status": response.status,
                    "time": end_time - start_time
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": str(e),
                "time": end_time - start_time
            }
    
    async def test_endpoint_performance(
        self,
        test_name: str,
        method: str,
        endpoint: str,
        num_requests: int = 100,
        concurrent_requests: int = 10,
        **request_kwargs
    ) -> PerformanceResult:
        """测试单个端点的性能"""
        print(f"\n开始测试: {test_name}")
        print(f"总请求数: {num_requests}, 并发数: {concurrent_requests}")
        
        url = f"{self.base_url}{endpoint}"
        results = []
        
        async with aiohttp.ClientSession() as session:
            # 创建请求任务
            tasks = []
            for i in range(num_requests):
                if i > 0 and i % concurrent_requests == 0:
                    # 批量执行并等待
                    batch_results = await asyncio.gather(*tasks)
                    results.extend(batch_results)
                    tasks = []
                
                task = self._make_request(session, method, url, **request_kwargs)
                tasks.append(task)
            
            # 执行剩余任务
            if tasks:
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
        
        # 分析结果
        successful_requests = sum(1 for r in results if r["success"])
        failed_requests = sum(1 for r in results if not r["success"])
        response_times = [r["time"] for r in results]
        
        # 计算统计数据
        result = PerformanceResult(
            test_name=test_name,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            min_time=min(response_times),
            max_time=max(response_times),
            mean_time=statistics.mean(response_times),
            median_time=statistics.median(response_times),
            p95_time=self._calculate_percentile(response_times, 95),
            p99_time=self._calculate_percentile(response_times, 99),
            throughput=num_requests / sum(response_times),
            error_rate=failed_requests / num_requests,
            timestamp=datetime.now()
        )
        
        self.results.append(result)
        self._print_result(result)
        
        return result
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _print_result(self, result: PerformanceResult):
        """打印测试结果"""
        print(f"\n{'='*50}")
        print(f"测试: {result.test_name}")
        print(f"{'='*50}")
        print(f"总请求数: {result.total_requests}")
        print(f"成功: {result.successful_requests} | 失败: {result.failed_requests}")
        print(f"错误率: {result.error_rate:.2%}")
        print(f"吞吐量: {result.throughput:.2f} 请求/秒")
        print(f"\n响应时间统计 (秒):")
        print(f"  最小: {result.min_time:.3f}")
        print(f"  最大: {result.max_time:.3f}")
        print(f"  平均: {result.mean_time:.3f}")
        print(f"  中位数: {result.median_time:.3f}")
        print(f"  P95: {result.p95_time:.3f}")
        print(f"  P99: {result.p99_time:.3f}")
    
    def generate_report(self, filename: str = "performance_report.json"):
        """生成性能报告"""
        report = {
            "test_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "results": [
                {
                    "test_name": r.test_name,
                    "metrics": {
                        "total_requests": r.total_requests,
                        "successful_requests": r.successful_requests,
                        "failed_requests": r.failed_requests,
                        "error_rate": r.error_rate,
                        "throughput": r.throughput,
                        "response_times": {
                            "min": r.min_time,
                            "max": r.max_time,
                            "mean": r.mean_time,
                            "median": r.median_time,
                            "p95": r.p95_time,
                            "p99": r.p99_time
                        }
                    }
                }
                for r in self.results
            ]
        }
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n性能报告已保存到: {filename}")


async def test_core_endpoints():
    """测试核心API端点性能"""
    tester = APIPerformanceTester(BASE_URL, HEADERS)
    
    # 1. 测试项目列表（GET请求）
    await tester.test_endpoint_performance(
        test_name="获取项目列表",
        method="GET",
        endpoint="/projects?limit=20",
        num_requests=100,
        concurrent_requests=10
    )
    
    # 2. 测试创建项目（POST请求）
    project_data = {
        "name": "性能测试项目",
        "description": "用于性能测试",
        "type": "research"
    }
    
    await tester.test_endpoint_performance(
        test_name="创建项目",
        method="POST",
        endpoint="/projects",
        num_requests=50,
        concurrent_requests=5,
        json=project_data
    )
    
    # 3. 测试认知对话（高负载端点）
    chat_data = {
        "message": "这是一个性能测试消息",
        "project_id": "test-project-id"
    }
    
    await tester.test_endpoint_performance(
        test_name="认知对话",
        method="POST",
        endpoint="/cognitive/chat",
        num_requests=30,
        concurrent_requests=3,
        json=chat_data
    )
    
    # 生成报告
    tester.generate_report()


if __name__ == "__main__":
    print("DPA API 性能测试")
    print("=" * 60)
    
    # 运行测试
    asyncio.run(test_core_endpoints())