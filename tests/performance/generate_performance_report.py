#!/usr/bin/env python
"""
性能测试报告生成器
汇总所有性能测试结果并生成综合报告
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Template

# 设置绘图风格
sns.set_style("whitegrid")
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class PerformanceReportGenerator:
    """性能测试报告生成器"""
    
    def __init__(self, results_dir: str = "."):
        self.results_dir = results_dir
        self.report_data = {
            "api_performance": None,
            "database_performance": None,
            "vector_search": None,
            "load_test": None
        }
    
    def load_test_results(self):
        """加载所有测试结果"""
        # 查找最新的测试报告
        files = os.listdir(self.results_dir)
        
        for report_type in self.report_data.keys():
            pattern = f"{report_type}_report_"
            matching_files = [f for f in files if f.startswith(pattern) and f.endswith('.json')]
            
            if matching_files:
                # 获取最新的文件
                latest_file = sorted(matching_files)[-1]
                with open(os.path.join(self.results_dir, latest_file), 'r') as f:
                    self.report_data[report_type] = json.load(f)
    
    def generate_charts(self):
        """生成性能图表"""
        charts_dir = "performance_charts"
        os.makedirs(charts_dir, exist_ok=True)
        
        # 1. API响应时间分布图
        if self.report_data["api_performance"]:
            self._plot_api_response_times(os.path.join(charts_dir, "api_response_times.png"))
        
        # 2. 数据库性能对比图
        if self.report_data["database_performance"]:
            self._plot_database_performance(os.path.join(charts_dir, "database_performance.png"))
        
        # 3. 向量搜索可扩展性图
        if self.report_data["vector_search"]:
            self._plot_vector_scalability(os.path.join(charts_dir, "vector_scalability.png"))
        
        # 4. 负载测试结果图
        if self.report_data["load_test"]:
            self._plot_load_test_results(os.path.join(charts_dir, "load_test_results.png"))
    
    def _plot_api_response_times(self, output_path: str):
        """绘制API响应时间图表"""
        data = self.report_data["api_performance"]["results"]["endpoint_tests"]
        
        endpoints = []
        mean_times = []
        p95_times = []
        
        for endpoint, metrics in data.items():
            if "response_times" in metrics:
                endpoints.append(endpoint)
                mean_times.append(metrics["response_times"]["mean"] * 1000)
                p95_times.append(metrics["response_times"]["p95"] * 1000)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(endpoints))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], mean_times, width, label='平均响应时间', alpha=0.8)
        ax.bar([i + width/2 for i in x], p95_times, width, label='P95响应时间', alpha=0.8)
        
        ax.set_xlabel('API端点')
        ax.set_ylabel('响应时间 (ms)')
        ax.set_title('API端点响应时间对比')
        ax.set_xticks(x)
        ax.set_xticklabels(endpoints, rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_database_performance(self, output_path: str):
        """绘制数据库性能对比图"""
        data = self.report_data["database_performance"]["summary"]
        
        # 准备数据
        databases = ['PostgreSQL', 'Qdrant', 'Redis', 'Neo4j']
        operations = {
            'PostgreSQL': ['插入', '查询'],
            'Qdrant': ['向量插入', '向量搜索'],
            'Redis': ['GET', 'SET'],
            'Neo4j': ['创建节点', '创建关系']
        }
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        for idx, db in enumerate(databases):
            ax = axes[idx]
            db_data = data[db.lower()]
            
            if db == 'Redis':
                # Redis显示OPS
                values = [
                    db_data.get('get_ops_per_second', 0),
                    db_data.get('set_ops_per_second', 0)
                ]
                ax.bar(operations[db], values)
                ax.set_ylabel('操作/秒')
            else:
                # 其他数据库显示延迟
                values = []
                for op in operations[db]:
                    for key, value in db_data.items():
                        if op.lower() in key.lower():
                            values.append(value)
                            break
                
                ax.bar(operations[db], values)
                ax.set_ylabel('延迟 (ms)')
            
            ax.set_title(f'{db} 性能')
            ax.set_xlabel('操作类型')
        
        plt.suptitle('数据库性能对比', fontsize=16)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_vector_scalability(self, output_path: str):
        """绘制向量搜索可扩展性图"""
        data = self.report_data["vector_search"]["results"]["scalability"]
        
        sizes = []
        mean_times = []
        p95_times = []
        
        for key, metrics in sorted(data.items()):
            sizes.append(metrics["dataset_size"])
            mean_times.append(metrics["mean_search_time_ms"])
            p95_times.append(metrics["p95_search_time_ms"])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(sizes, mean_times, 'o-', label='平均搜索时间', linewidth=2, markersize=8)
        ax.plot(sizes, p95_times, 's-', label='P95搜索时间', linewidth=2, markersize=8)
        
        ax.set_xlabel('数据集大小')
        ax.set_ylabel('搜索时间 (ms)')
        ax.set_title('向量搜索可扩展性测试')
        ax.set_xscale('log')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_load_test_results(self, output_path: str):
        """绘制负载测试结果图"""
        data = self.report_data["load_test"]
        
        # 准备端点数据
        endpoints_data = []
        for endpoint, metrics in data["endpoints"].items():
            endpoints_data.append({
                "endpoint": endpoint,
                "requests": metrics["num_requests"],
                "failures": metrics["num_failures"],
                "avg_time": metrics["avg_response_time"],
                "p95_time": metrics["percentile_95"]
            })
        
        # 按请求数排序
        endpoints_data.sort(key=lambda x: x["requests"], reverse=True)
        top_endpoints = endpoints_data[:10]  # 只显示前10个
        
        # 创建子图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 图1：请求分布
        endpoints = [e["endpoint"] for e in top_endpoints]
        requests = [e["requests"] for e in top_endpoints]
        
        ax1.barh(endpoints, requests)
        ax1.set_xlabel('请求数')
        ax1.set_title('端点请求分布')
        
        # 图2：响应时间
        avg_times = [e["avg_time"] for e in top_endpoints]
        p95_times = [e["p95_time"] for e in top_endpoints]
        
        x = range(len(endpoints))
        width = 0.35
        
        ax2.barh([i - width/2 for i in x], avg_times, width, label='平均时间')
        ax2.barh([i + width/2 for i in x], p95_times, width, label='P95时间')
        ax2.set_yticks(x)
        ax2.set_yticklabels(endpoints)
        ax2.set_xlabel('响应时间 (ms)')
        ax2.set_title('端点响应时间')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_html_report(self):
        """生成HTML报告"""
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>DPA性能测试报告</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #333; }
        .summary { background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .metric { display: inline-block; margin: 10px 20px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .chart { margin: 20px 0; text-align: center; }
        .recommendation { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 10px 0; }
        .pass { color: #28a745; }
        .fail { color: #dc3545; }
    </style>
</head>
<body>
    <h1>DPA性能测试报告</h1>
    <p>生成时间: {{ report_date }}</p>
    
    <div class="summary">
        <h2>测试摘要</h2>
        <div class="metric">
            <div class="metric-value">{{ api_rps }}</div>
            <div class="metric-label">API RPS</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ api_p95 }}ms</div>
            <div class="metric-label">API P95响应时间</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ vector_qps }}</div>
            <div class="metric-label">向量搜索QPS</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ success_rate }}%</div>
            <div class="metric-label">成功率</div>
        </div>
    </div>
    
    <h2>API性能测试</h2>
    <div class="chart">
        <img src="performance_charts/api_response_times.png" alt="API响应时间">
    </div>
    
    <h3>关键指标</h3>
    <table>
        <tr>
            <th>端点</th>
            <th>请求数</th>
            <th>成功率</th>
            <th>平均响应时间</th>
            <th>P95响应时间</th>
        </tr>
        {% for endpoint in api_endpoints %}
        <tr>
            <td>{{ endpoint.name }}</td>
            <td>{{ endpoint.requests }}</td>
            <td class="{{ 'pass' if endpoint.success_rate >= 99 else 'fail' }}">{{ endpoint.success_rate }}%</td>
            <td>{{ endpoint.avg_time }}ms</td>
            <td>{{ endpoint.p95_time }}ms</td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>数据库性能测试</h2>
    <div class="chart">
        <img src="performance_charts/database_performance.png" alt="数据库性能">
    </div>
    
    <h2>向量搜索性能</h2>
    <div class="chart">
        <img src="performance_charts/vector_scalability.png" alt="向量搜索可扩展性">
    </div>
    
    <h2>负载测试结果</h2>
    <div class="chart">
        <img src="performance_charts/load_test_results.png" alt="负载测试结果">
    </div>
    
    <h2>性能基准对照</h2>
    <table>
        <tr>
            <th>指标</th>
            <th>目标值</th>
            <th>实际值</th>
            <th>状态</th>
        </tr>
        {% for benchmark in benchmarks %}
        <tr>
            <td>{{ benchmark.name }}</td>
            <td>{{ benchmark.target }}</td>
            <td>{{ benchmark.actual }}</td>
            <td class="{{ 'pass' if benchmark.passed else 'fail' }}">
                {{ '✓ 通过' if benchmark.passed else '✗ 未达标' }}
            </td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>优化建议</h2>
    {% for rec in recommendations %}
    <div class="recommendation">
        <strong>{{ rec.title }}</strong><br>
        {{ rec.description }}
    </div>
    {% endfor %}
    
    <h2>结论</h2>
    <p>{{ conclusion }}</p>
</body>
</html>
        """)
        
        # 准备模板数据
        context = self._prepare_report_context()
        
        # 生成HTML
        html_content = template.render(**context)
        
        # 保存报告
        report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"HTML报告已生成: {report_file}")
    
    def _prepare_report_context(self) -> Dict[str, Any]:
        """准备报告上下文数据"""
        context = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_endpoints": [],
            "benchmarks": [],
            "recommendations": []
        }
        
        # API性能数据
        if self.report_data["api_performance"]:
            api_data = self.report_data["api_performance"]["results"]["endpoint_tests"]
            
            for endpoint, metrics in api_data.items():
                if "response_times" in metrics:
                    context["api_endpoints"].append({
                        "name": endpoint,
                        "requests": metrics.get("total_requests", 0),
                        "success_rate": round(metrics.get("success_rate", 0), 1),
                        "avg_time": round(metrics["response_times"]["mean"] * 1000, 2),
                        "p95_time": round(metrics["response_times"]["p95"] * 1000, 2)
                    })
            
            # 计算总体指标
            total_requests = sum(m.get("total_requests", 0) for m in api_data.values())
            total_duration = sum(m.get("duration_seconds", 0) for m in api_data.values())
            context["api_rps"] = round(total_requests / total_duration if total_duration > 0 else 0, 1)
            
            p95_times = [m["response_times"]["p95"] * 1000 for m in api_data.values() if "response_times" in m]
            context["api_p95"] = round(sum(p95_times) / len(p95_times) if p95_times else 0, 1)
        
        # 向量搜索性能
        if self.report_data["vector_search"]:
            context["vector_qps"] = round(
                self.report_data["vector_search"]["results"]["search_performance"]["top_10"]["queries_per_second"], 1
            )
        
        # 负载测试
        if self.report_data["load_test"]:
            total_reqs = self.report_data["load_test"]["total_requests"]
            total_fails = self.report_data["load_test"]["total_failures"]
            context["success_rate"] = round((1 - total_fails / total_reqs) * 100 if total_reqs > 0 else 0, 1)
        
        # 性能基准
        context["benchmarks"] = [
            {
                "name": "API响应时间P95 < 200ms",
                "target": "< 200ms",
                "actual": f"{context.get('api_p95', 0)}ms",
                "passed": context.get("api_p95", 999) < 200
            },
            {
                "name": "系统吞吐量 > 1000 RPS",
                "target": "> 1000 RPS",
                "actual": f"{context.get('api_rps', 0)} RPS",
                "passed": context.get("api_rps", 0) > 1000
            },
            {
                "name": "向量搜索 > 100 QPS",
                "target": "> 100 QPS",
                "actual": f"{context.get('vector_qps', 0)} QPS",
                "passed": context.get("vector_qps", 0) > 100
            },
            {
                "name": "系统可用性 > 99.9%",
                "target": "> 99.9%",
                "actual": f"{context.get('success_rate', 0)}%",
                "passed": context.get("success_rate", 0) > 99.9
            }
        ]
        
        # 生成优化建议
        if context["api_p95"] > 200:
            context["recommendations"].append({
                "title": "API响应时间优化",
                "description": "P95响应时间超过200ms，建议优化数据库查询、增加缓存或扩展服务实例。"
            })
        
        if context.get("api_rps", 0) < 1000:
            context["recommendations"].append({
                "title": "提升系统吞吐量",
                "description": "当前RPS未达到1000的目标，建议增加工作进程数、优化代码热点或使用更高性能的服务器。"
            })
        
        # 结论
        passed_count = sum(1 for b in context["benchmarks"] if b["passed"])
        total_count = len(context["benchmarks"])
        
        if passed_count == total_count:
            context["conclusion"] = "所有性能指标均达到预期目标，系统性能表现优秀。"
        elif passed_count >= total_count * 0.7:
            context["conclusion"] = f"大部分性能指标达标（{passed_count}/{total_count}），建议关注未达标项进行优化。"
        else:
            context["conclusion"] = f"性能测试发现多项指标未达标（{passed_count}/{total_count}通过），需要进行性能优化。"
        
        return context


def main():
    """主函数"""
    generator = PerformanceReportGenerator()
    
    print("=== DPA性能测试报告生成器 ===")
    
    # 加载测试结果
    print("\n1. 加载测试结果...")
    generator.load_test_results()
    
    # 生成图表
    print("2. 生成性能图表...")
    generator.generate_charts()
    
    # 生成HTML报告
    print("3. 生成HTML报告...")
    generator.generate_html_report()
    
    print("\n报告生成完成！")


if __name__ == "__main__":
    main()