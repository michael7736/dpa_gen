#!/usr/bin/env python
"""
负载测试运行器
使用Locust进行分布式负载测试
"""

import os
import sys
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
import gevent

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class DPAUser(HttpUser):
    """DPA系统用户行为模拟"""
    
    wait_time = between(1, 3)  # 用户思考时间
    
    def on_start(self):
        """用户开始时的行为"""
        # 创建测试项目
        response = self.client.post("/api/v1/projects", json={
            "name": f"负载测试项目_{datetime.now().timestamp()}",
            "description": "用于负载测试"
        })
        if response.status_code == 200:
            self.project_id = response.json()["id"]
        else:
            self.project_id = None
    
    @task(3)
    def view_homepage(self):
        """访问首页"""
        self.client.get("/")
    
    @task(5)
    def health_check(self):
        """健康检查"""
        self.client.get("/health")
    
    @task(10)
    def search_documents(self):
        """搜索文档"""
        self.client.post("/api/v1/search", json={
            "query": "测试查询",
            "limit": 10
        })
    
    @task(8)
    def upload_document(self):
        """上传文档"""
        if self.project_id:
            self.client.post("/api/v1/documents", json={
                "project_id": self.project_id,
                "title": f"测试文档_{datetime.now().timestamp()}",
                "content": "这是测试文档内容" * 100,
                "type": "text"
            })
    
    @task(6)
    def ask_question(self):
        """问答测试"""
        self.client.post("/api/v1/qa/ask", json={
            "question": "什么是负载测试？",
            "project_id": self.project_id
        })
    
    @task(2)
    def view_api_docs(self):
        """查看API文档"""
        self.client.get("/docs")


class AdminUser(HttpUser):
    """管理员用户行为"""
    
    wait_time = between(2, 5)
    
    @task(1)
    def view_metrics(self):
        """查看监控指标"""
        self.client.get("/metrics")
    
    @task(2)
    def manage_projects(self):
        """管理项目"""
        self.client.get("/api/v1/projects")
    
    @task(1)
    def system_stats(self):
        """查看系统统计"""
        self.client.get("/api/v1/admin/stats")


def run_load_test(
    host: str = "http://localhost:8000",
    users: int = 100,
    spawn_rate: int = 10,
    run_time: int = 300
):
    """运行负载测试"""
    
    # 设置日志
    setup_logging("INFO", None)
    
    # 创建环境
    env = Environment(user_classes=[DPAUser, AdminUser], host=host)
    
    # 启动Web UI
    env.create_local_runner()
    
    # 启动测试
    env.runner.start(users, spawn_rate=spawn_rate)
    
    # 运行指定时间
    gevent.spawn_later(run_time, lambda: env.runner.quit())
    
    # 启动统计
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history, env.runner)
    
    # 等待完成
    env.runner.greenlet.join()
    
    # 生成报告
    generate_report(env.stats)


def generate_report(stats):
    """生成负载测试报告"""
    report = {
        "test_date": datetime.now().isoformat(),
        "total_requests": stats.total.num_requests,
        "total_failures": stats.total.num_failures,
        "average_response_time": stats.total.avg_response_time,
        "min_response_time": stats.total.min_response_time,
        "max_response_time": stats.total.max_response_time,
        "rps": stats.total.current_rps,
        "endpoints": {}
    }
    
    # 收集每个端点的统计
    for name, entry in stats.entries.items():
        report["endpoints"][name] = {
            "num_requests": entry.num_requests,
            "num_failures": entry.num_failures,
            "avg_response_time": entry.avg_response_time,
            "min_response_time": entry.min_response_time,
            "max_response_time": entry.max_response_time,
            "median_response_time": entry.median_response_time,
            "percentile_95": entry.get_response_time_percentile(0.95),
            "percentile_99": entry.get_response_time_percentile(0.99)
        }
    
    # 保存报告
    import json
    report_file = f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n负载测试报告已保存到: {report_file}")
    
    # 打印摘要
    print("\n=== 负载测试摘要 ===")
    print(f"总请求数: {report['total_requests']}")
    print(f"失败请求: {report['total_failures']}")
    print(f"平均响应时间: {report['average_response_time']:.2f} ms")
    print(f"RPS: {report['rps']:.2f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DPA负载测试")
    parser.add_argument("--host", default="http://localhost:8000", help="目标主机")
    parser.add_argument("--users", type=int, default=100, help="并发用户数")
    parser.add_argument("--spawn-rate", type=int, default=10, help="用户增长速率")
    parser.add_argument("--time", type=int, default=300, help="测试时长(秒)")
    
    args = parser.parse_args()
    
    print(f"开始负载测试: {args.host}")
    print(f"并发用户: {args.users}")
    print(f"增长速率: {args.spawn_rate}/秒")
    print(f"测试时长: {args.time}秒")
    
    run_load_test(
        host=args.host,
        users=args.users,
        spawn_rate=args.spawn_rate,
        run_time=args.time
    )