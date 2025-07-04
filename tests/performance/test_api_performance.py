#!/usr/bin/env python
"""
API性能基准测试
测试各个端点的响应时间、吞吐量和并发性能
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import json

import httpx
import aiofiles
from tqdm import tqdm

from ...src.config.settings import get_settings

settings = get_settings()


class PerformanceMetrics:
    """性能指标记录器"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None
    
    def add_response(self, response_time: float, status_code: int):
        """添加响应记录"""
        self.response_times.append(response_time)
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
    
    def add_error(self, error: str):
        """添加错误记录"""
        self.errors.append(error)
    
    def calculate_stats(self) -> Dict[str, Any]:
        """计算统计数据"""
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        total_requests = len(self.response_times) + len(self.errors)
        successful_requests = len(self.response_times)
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": len(self.errors),
            "success_rate": successful_requests / total_requests * 100 if total_requests > 0 else 0,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            "requests_per_second": total_requests / ((self.end_time - self.start_time).total_seconds()) if self.end_time else 0,
            "response_times": {
                "min": min(sorted_times),
                "max": max(sorted_times),
                "mean": statistics.mean(sorted_times),
                "median": statistics.median(sorted_times),
                "p95": sorted_times[int(len(sorted_times) * 0.95)],
                "p99": sorted_times[int(len(sorted_times) * 0.99)],
                "stdev": statistics.stdev(sorted_times) if len(sorted_times) > 1 else 0
            },
            "status_codes": self.status_codes,
            "errors": self.errors[:10]  # 只显示前10个错误
        }


class APIPerformanceTester:
    """API性能测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.test_data = self._prepare_test_data()
    
    def _prepare_test_data(self) -> Dict[str, Any]:
        """准备测试数据"""
        return {
            "project": {
                "name": f"性能测试项目_{int(time.time())}",
                "description": "用于性能测试的项目"
            },
            "document": {
                "title": "测试文档",
                "content": "这是一个用于性能测试的文档内容。" * 100,
                "type": "text"
            },
            "query": {
                "question": "什么是性能测试？",
                "k": 5
            }
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=50)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.aclose()
    
    async def test_endpoint(
        self,
        method: str,
        path: str,
        data: Dict[str, Any] = None,
        concurrent_requests: int = 10,
        total_requests: int = 100
    ) -> PerformanceMetrics:
        """测试单个端点"""
        metrics = PerformanceMetrics()
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request():
            async with semaphore:
                try:
                    start = time.time()
                    
                    if method == "GET":
                        response = await self.client.get(path)
                    elif method == "POST":
                        response = await self.client.post(path, json=data)
                    elif method == "PUT":
                        response = await self.client.put(path, json=data)
                    elif method == "DELETE":
                        response = await self.client.delete(path)
                    else:
                        raise ValueError(f"不支持的方法: {method}")
                    
                    response_time = time.time() - start
                    metrics.add_response(response_time, response.status_code)
                    
                except Exception as e:
                    metrics.add_error(str(e))
        
        # 记录开始时间
        metrics.start_time = datetime.now()
        
        # 创建所有请求任务
        tasks = [make_request() for _ in range(total_requests)]
        
        # 使用进度条执行
        with tqdm(total=total_requests, desc=f"{method} {path}") as pbar:
            for coro in asyncio.as_completed(tasks):
                await coro
                pbar.update(1)
        
        # 记录结束时间
        metrics.end_time = datetime.now()
        
        return metrics
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """运行完整的性能测试套件"""
        results = {}
        
        print("\n=== API性能基准测试 ===\n")
        
        # 1. 测试健康检查端点（预热）
        print("1. 预热测试...")
        await self.test_endpoint("GET", "/health", concurrent_requests=5, total_requests=20)
        
        # 2. 测试基础端点
        print("\n2. 测试基础端点...")
        endpoints = [
            ("GET", "/health", None, 50, 1000),
            ("GET", "/", None, 50, 500),
            ("GET", "/api/v1/demo/basic", None, 30, 300),
        ]
        
        for method, path, data, concurrent, total in endpoints:
            metrics = await self.test_endpoint(method, path, data, concurrent, total)
            results[f"{method} {path}"] = metrics.calculate_stats()
            await asyncio.sleep(1)  # 避免过载
        
        # 3. 测试CRUD操作
        print("\n3. 测试CRUD操作...")
        
        # 创建项目
        create_metrics = await self.test_endpoint(
            "POST", "/api/v1/projects",
            self.test_data["project"],
            concurrent_requests=10,
            total_requests=100
        )
        results["POST /api/v1/projects"] = create_metrics.calculate_stats()
        
        # 4. 测试限流端点
        print("\n4. 测试限流端点...")
        rate_limit_metrics = await self.test_endpoint(
            "GET", "/api/v1/demo/limited",
            concurrent_requests=20,
            total_requests=50
        )
        results["Rate Limited Endpoint"] = rate_limit_metrics.calculate_stats()
        
        return results
    
    async def test_concurrent_users(self, user_counts: List[int] = [10, 50, 100, 200]) -> Dict[str, Any]:
        """测试不同并发用户数下的性能"""
        results = {}
        
        print("\n=== 并发用户测试 ===\n")
        
        for users in user_counts:
            print(f"\n测试 {users} 并发用户...")
            metrics = await self.test_endpoint(
                "GET", "/api/v1/demo/basic",
                concurrent_requests=users,
                total_requests=users * 10
            )
            results[f"{users}_users"] = metrics.calculate_stats()
            await asyncio.sleep(2)
        
        return results
    
    async def test_payload_sizes(self) -> Dict[str, Any]:
        """测试不同负载大小的性能"""
        results = {}
        
        print("\n=== 负载大小测试 ===\n")
        
        sizes = [1, 10, 50, 100, 500]  # KB
        
        for size_kb in sizes:
            print(f"\n测试 {size_kb}KB 负载...")
            
            # 生成指定大小的内容
            content = "x" * (size_kb * 1024)
            data = {
                "title": f"测试文档_{size_kb}KB",
                "content": content,
                "type": "text"
            }
            
            metrics = await self.test_endpoint(
                "POST", "/api/v1/documents",
                data,
                concurrent_requests=10,
                total_requests=50
            )
            results[f"{size_kb}KB"] = metrics.calculate_stats()
            await asyncio.sleep(1)
        
        return results
    
    async def test_sustained_load(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """持续负载测试"""
        print(f"\n=== 持续负载测试 ({duration_seconds}秒) ===\n")
        
        metrics = PerformanceMetrics()
        metrics.start_time = datetime.now()
        
        async def continuous_requests():
            end_time = time.time() + duration_seconds
            while time.time() < end_time:
                try:
                    start = time.time()
                    response = await self.client.get("/api/v1/demo/basic")
                    response_time = time.time() - start
                    metrics.add_response(response_time, response.status_code)
                except Exception as e:
                    metrics.add_error(str(e))
                await asyncio.sleep(0.1)  # 每秒10个请求
        
        # 创建多个并发任务
        tasks = [continuous_requests() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        metrics.end_time = datetime.now()
        return metrics.calculate_stats()


async def generate_performance_report(results: Dict[str, Any], output_file: str):
    """生成性能测试报告"""
    report = {
        "test_date": datetime.now().isoformat(),
        "environment": {
            "api_url": "http://localhost:8000",
            "version": "1.0.0"
        },
        "results": results,
        "summary": {
            "total_endpoints_tested": len(results.get("endpoint_tests", {})),
            "average_response_time": statistics.mean([
                test.get("response_times", {}).get("mean", 0)
                for test in results.get("endpoint_tests", {}).values()
                if "response_times" in test
            ]),
            "recommendations": []
        }
    }
    
    # 添加建议
    for endpoint, metrics in results.get("endpoint_tests", {}).items():
        if metrics.get("response_times", {}).get("p95", 0) > 1.0:
            report["summary"]["recommendations"].append(
                f"{endpoint}: P95响应时间超过1秒，建议优化"
            )
        if metrics.get("success_rate", 100) < 99:
            report["summary"]["recommendations"].append(
                f"{endpoint}: 成功率低于99%，需要检查稳定性"
            )
    
    # 保存报告
    async with aiofiles.open(output_file, "w") as f:
        await f.write(json.dumps(report, indent=2, ensure_ascii=False))
    
    print(f"\n性能测试报告已保存到: {output_file}")


async def main():
    """主测试函数"""
    results = {
        "endpoint_tests": {},
        "concurrent_users": {},
        "payload_sizes": {},
        "sustained_load": {}
    }
    
    async with APIPerformanceTester() as tester:
        # 1. 端点性能测试
        endpoint_results = await tester.run_performance_tests()
        results["endpoint_tests"] = endpoint_results
        
        # 2. 并发用户测试
        concurrent_results = await tester.test_concurrent_users()
        results["concurrent_users"] = concurrent_results
        
        # 3. 负载大小测试
        # payload_results = await tester.test_payload_sizes()
        # results["payload_sizes"] = payload_results
        
        # 4. 持续负载测试
        sustained_results = await tester.test_sustained_load(duration_seconds=30)
        results["sustained_load"] = sustained_results
    
    # 生成报告
    report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    await generate_performance_report(results, report_file)
    
    # 打印摘要
    print("\n=== 测试摘要 ===")
    for endpoint, metrics in results["endpoint_tests"].items():
        if "response_times" in metrics:
            print(f"\n{endpoint}:")
            print(f"  - 成功率: {metrics['success_rate']:.1f}%")
            print(f"  - 平均响应时间: {metrics['response_times']['mean']:.3f}s")
            print(f"  - P95响应时间: {metrics['response_times']['p95']:.3f}s")
            print(f"  - 吞吐量: {metrics['requests_per_second']:.1f} req/s")


if __name__ == "__main__":
    asyncio.run(main())