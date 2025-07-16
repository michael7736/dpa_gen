#!/usr/bin/env python3
"""
性能测试脚本
测试系统的响应时间、并发能力和资源使用
"""

import asyncio
import httpx
import time
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 配置
BASE_URL = "http://localhost:8200"
USER_ID = "u1"
HEADERS = {"X-USER-ID": USER_ID}

# 测试结果
performance_results = {
    "response_times": [],
    "concurrent_results": [],
    "memory_usage": [],
    "errors": []
}


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"⚡ {title}")
    print("=" * 60)


def print_metric(name: str, value: float, unit: str = "ms", threshold: float = None):
    """打印性能指标"""
    status = "✅" if threshold is None or value <= threshold else "⚠️"
    print(f"{status} {name}: {value:.1f}{unit}")
    if threshold and value > threshold:
        print(f"   警告: 超过阈值 {threshold}{unit}")


async def test_response_times(client: httpx.AsyncClient):
    """测试响应时间"""
    print_header("响应时间测试")
    
    endpoints = [
        ("健康检查", "GET", "/health", None),
        ("项目列表", "GET", "/api/v1/projects", HEADERS),
        ("AAG快速略读", "POST", "/api/v1/aag/skim", {
            **HEADERS,
            "Content-Type": "application/json"
        }),
        ("基础问答", "POST", "/api/v1/qa/answer", {
            **HEADERS,
            "Content-Type": "application/json"
        })
    ]
    
    for name, method, endpoint, headers in endpoints:
        times = []
        errors = 0
        
        # 运行5次测试取平均值
        for i in range(5):
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = await client.get(f"{BASE_URL}{endpoint}", headers=headers or {})
                else:
                    test_data = {}
                    if "skim" in endpoint:
                        test_data = {
                            "skim_request": {
                                "document_id": "perf_test",
                                "document_content": "性能测试文档内容",
                                "document_type": "test"
                            }
                        }
                    elif "qa" in endpoint:
                        test_data = {
                            "question": "性能测试问题",
                            "project_id": "test_project"
                        }
                    
                    response = await client.post(
                        f"{BASE_URL}{endpoint}",
                        headers=headers or {},
                        json=test_data
                    )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code in [200, 201]:
                    times.append(response_time)
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                performance_results["errors"].append(f"{name}: {str(e)}")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\n{name}:")
            print_metric("  平均响应时间", avg_time, "ms", 2000)
            print_metric("  最快响应时间", min_time, "ms")
            print_metric("  最慢响应时间", max_time, "ms")
            
            if errors > 0:
                print(f"  ❌ 错误次数: {errors}/5")
            
            performance_results["response_times"].append({
                "endpoint": name,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "errors": errors
            })


async def test_concurrent_requests(client: httpx.AsyncClient):
    """测试并发请求"""
    print_header("并发性能测试")
    
    async def make_request():
        """发起单个请求"""
        try:
            start_time = time.time()
            response = await client.get(f"{BASE_URL}/health")
            end_time = time.time()
            
            return {
                "success": response.status_code == 200,
                "response_time": (end_time - start_time) * 1000,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "response_time": 0,
                "error": str(e)
            }
    
    # 测试不同并发级别
    concurrency_levels = [1, 5, 10, 20]
    
    for concurrency in concurrency_levels:
        print(f"\n测试并发级别: {concurrency}")
        
        start_time = time.time()
        
        # 创建并发任务
        tasks = [make_request() for _ in range(concurrency)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # 分析结果
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        if successful:
            avg_response_time = statistics.mean([r["response_time"] for r in successful])
            throughput = len(successful) / (total_time / 1000)  # requests per second
            
            print_metric("  总耗时", total_time, "ms")
            print_metric("  平均响应时间", avg_response_time, "ms", 1000)
            print_metric("  吞吐量", throughput, " req/s")
            print(f"  ✅ 成功: {len(successful)}/{concurrency}")
            
            if failed:
                print(f"  ❌ 失败: {len(failed)}/{concurrency}")
        
        performance_results["concurrent_results"].append({
            "concurrency": concurrency,
            "total_time": total_time,
            "successful": len(successful),
            "failed": len(failed),
            "avg_response_time": avg_response_time if successful else 0,
            "throughput": throughput if successful else 0
        })


async def test_stress_scenario(client: httpx.AsyncClient):
    """压力测试场景"""
    print_header("压力测试")
    
    print("执行30秒压力测试...")
    
    start_time = time.time()
    request_count = 0
    error_count = 0
    response_times = []
    
    while time.time() - start_time < 30:  # 运行30秒
        try:
            req_start = time.time()
            response = await client.get(f"{BASE_URL}/health")
            req_end = time.time()
            
            request_count += 1
            response_times.append((req_end - req_start) * 1000)
            
            if response.status_code != 200:
                error_count += 1
                
        except Exception:
            error_count += 1
        
        # 小延迟避免过度压力
        await asyncio.sleep(0.1)
    
    total_time = time.time() - start_time
    
    if response_times:
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        throughput = request_count / total_time
        
        print(f"\n压力测试结果 (运行时间: {total_time:.1f}秒):")
        print_metric("  总请求数", request_count, "")
        print_metric("  错误数", error_count, "")
        print_metric("  成功率", (1 - error_count/request_count) * 100, "%")
        print_metric("  平均响应时间", avg_response_time, "ms", 500)
        print_metric("  95%响应时间", p95_response_time, "ms", 1000)
        print_metric("  平均吞吐量", throughput, " req/s")


async def test_memory_usage():
    """测试内存使用情况"""
    print_header("资源使用监控")
    
    try:
        import psutil
        import os
        
        # 获取当前进程信息
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=1)
        
        print(f"测试进程资源使用:")
        print_metric("  内存使用", memory_info.rss / 1024 / 1024, "MB")
        print_metric("  CPU使用率", cpu_percent, "%")
        
        # 尝试获取系统整体信息
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=1)
        
        print(f"\n系统整体资源:")
        print_metric("  系统内存使用率", system_memory.percent, "%")
        print_metric("  系统CPU使用率", system_cpu, "%")
        
    except ImportError:
        print("⚠️  psutil未安装，跳过资源监控")
    except Exception as e:
        print(f"❌ 资源监控失败: {e}")


def generate_performance_report():
    """生成性能报告"""
    print_header("📊 性能测试报告")
    
    # 响应时间总结
    if performance_results["response_times"]:
        print("\n响应时间总结:")
        for result in performance_results["response_times"]:
            status = "✅" if result["avg_time"] <= 2000 else "⚠️"
            print(f"{status} {result['endpoint']}: {result['avg_time']:.1f}ms")
    
    # 并发性能总结
    if performance_results["concurrent_results"]:
        print("\n并发性能总结:")
        for result in performance_results["concurrent_results"]:
            success_rate = result["successful"] / (result["successful"] + result["failed"]) * 100
            print(f"  并发{result['concurrency']}: {result['throughput']:.1f} req/s, 成功率 {success_rate:.1f}%")
    
    # 性能评级
    avg_response_times = [r["avg_time"] for r in performance_results["response_times"]]
    if avg_response_times:
        overall_avg = statistics.mean(avg_response_times)
        
        if overall_avg <= 500:
            grade = "🏆 优秀"
        elif overall_avg <= 1000:
            grade = "✅ 良好"
        elif overall_avg <= 2000:
            grade = "⚠️  一般"
        else:
            grade = "❌ 需要优化"
        
        print(f"\n整体性能评级: {grade}")
        print(f"平均响应时间: {overall_avg:.1f}ms")
    
    # 优化建议
    print(f"\n🔧 优化建议:")
    
    slow_endpoints = [r for r in performance_results["response_times"] if r["avg_time"] > 1000]
    if slow_endpoints:
        print("  • 以下端点响应时间较慢，建议优化:")
        for endpoint in slow_endpoints:
            print(f"    - {endpoint['endpoint']}: {endpoint['avg_time']:.1f}ms")
    
    high_error_endpoints = [r for r in performance_results["response_times"] if r["errors"] > 0]
    if high_error_endpoints:
        print("  • 以下端点存在错误，需要检查:")
        for endpoint in high_error_endpoints:
            print(f"    - {endpoint['endpoint']}: {endpoint['errors']} 错误")
    
    if not slow_endpoints and not high_error_endpoints:
        print("  • 系统性能表现良好，无需特别优化")


async def main():
    """运行性能测试"""
    print("\n" + "⚡" * 20)
    print("DPA系统性能测试")
    print("⚡" * 20)
    print(f"目标地址: {BASE_URL}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 响应时间测试
        await test_response_times(client)
        
        # 2. 并发性能测试
        await test_concurrent_requests(client)
        
        # 3. 压力测试
        await test_stress_scenario(client)
        
        # 4. 资源使用监控
        await test_memory_usage()
        
        # 5. 生成报告
        generate_performance_report()
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())