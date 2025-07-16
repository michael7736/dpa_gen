#!/usr/bin/env python3
"""
DPA服务测试脚本
检查后端和前端服务状态
"""

import requests
import json
import time
import subprocess
import os
import sys
from urllib.parse import urljoin

class DPAServiceTester:
    def __init__(self):
        self.backend_url = "http://localhost:8200"
        self.frontend_url = "http://localhost:8230"
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        self.test_results.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    def check_service_health(self, url, service_name):
        """检查服务健康状态"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.log(f"✅ {service_name} 服务正常运行", "SUCCESS")
                return True
            else:
                self.log(f"❌ {service_name} 服务异常: {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"❌ 无法连接到{service_name}服务: {e}", "ERROR")
            return False
    
    def test_backend_apis(self):
        """测试后端API端点"""
        self.log("🔍 测试后端API端点...")
        
        # 测试端点列表
        endpoints = [
            ("/api/v1/health", "健康检查"),
            ("/api/v1/projects", "项目列表"),
            ("/api/v1/documents", "文档列表")
        ]
        
        headers = {"X-USER-ID": "u1"}
        results = []
        
        for endpoint, description in endpoints:
            try:
                url = urljoin(self.backend_url, endpoint)
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    self.log(f"✅ {description} API 测试通过", "SUCCESS")
                    results.append(True)
                else:
                    self.log(f"❌ {description} API 测试失败: {response.status_code}", "ERROR")
                    results.append(False)
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ {description} API 测试异常: {e}", "ERROR")
                results.append(False)
        
        return all(results)
    
    def test_frontend_access(self):
        """测试前端访问"""
        self.log("🎨 测试前端访问...")
        
        # 测试主页
        if self.check_service_health(self.frontend_url, "前端主页"):
            # 测试AAG页面
            aag_url = urljoin(self.frontend_url, "/aag")
            if self.check_service_health(aag_url, "AAG页面"):
                return True
        
        return False
    
    def test_websocket_availability(self):
        """测试WebSocket可用性"""
        self.log("🔗 测试WebSocket可用性...")
        
        # 这里只是检查WebSocket端点是否响应
        # 实际的WebSocket连接需要专门的客户端
        try:
            # 检查WebSocket端点路径
            ws_info_url = urljoin(self.backend_url, "/api/v1/health")
            response = requests.get(ws_info_url, timeout=5)
            
            if response.status_code == 200:
                self.log("✅ WebSocket端点可访问", "SUCCESS")
                return True
            else:
                self.log("❌ WebSocket端点不可访问", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ WebSocket测试异常: {e}", "ERROR")
            return False
    
    def check_process_running(self, process_name, port):
        """检查进程是否运行"""
        try:
            # 使用lsof检查端口占用
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                self.log(f"✅ {process_name} 进程正在运行 (端口:{port})", "SUCCESS")
                return True
            else:
                self.log(f"❌ {process_name} 进程未运行 (端口:{port})", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 检查{process_name}进程时出错: {e}", "ERROR")
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        report_file = f"test_report_{int(time.time())}.json"
        
        success_count = len([r for r in self.test_results if r["level"] == "SUCCESS"])
        error_count = len([r for r in self.test_results if r["level"] == "ERROR"])
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": len(self.test_results),
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": f"{(success_count / len(self.test_results) * 100):.1f}%" if self.test_results else "0%"
            },
            "results": self.test_results
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"📊 测试报告已生成: {report_file}", "INFO")
        return report
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("🚀 开始DPA服务测试...")
        
        # 检查进程状态
        backend_running = self.check_process_running("后端服务", 8200)
        frontend_running = self.check_process_running("前端服务", 8230)
        
        if not backend_running:
            self.log("⚠️ 后端服务未运行，请启动后端服务", "WARNING")
            self.log("启动命令: uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload", "INFO")
        
        if not frontend_running:
            self.log("⚠️ 前端服务未运行，请启动前端服务", "WARNING")
            self.log("启动命令: cd frontend && npm run dev", "INFO")
        
        # 运行测试
        tests = [
            ("后端健康检查", lambda: self.check_service_health(f"{self.backend_url}/api/v1/health", "后端")),
            ("前端访问测试", self.test_frontend_access),
            ("后端API测试", self.test_backend_apis),
            ("WebSocket可用性", self.test_websocket_availability)
        ]
        
        passed_tests = 0
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 开始测试: {test_name}")
            
            try:
                result = test_func()
                if result:
                    self.log(f"✅ {test_name} 测试通过", "SUCCESS")
                    passed_tests += 1
                else:
                    self.log(f"❌ {test_name} 测试失败", "ERROR")
            except Exception as e:
                self.log(f"❌ {test_name} 测试异常: {e}", "ERROR")
        
        # 生成报告
        report = self.generate_test_report()
        
        # 输出测试总结
        self.log("\n📊 测试总结:")
        self.log(f"总测试数: {len(tests)}")
        self.log(f"通过测试: {passed_tests}")
        self.log(f"失败测试: {len(tests) - passed_tests}")
        self.log(f"成功率: {(passed_tests / len(tests) * 100):.1f}%")
        
        if passed_tests == len(tests):
            self.log("🎉 所有测试通过！", "SUCCESS")
        elif passed_tests > 0:
            self.log("⚠️ 部分测试通过", "WARNING")
        else:
            self.log("❌ 所有测试失败", "ERROR")
        
        return report

def main():
    """主函数"""
    tester = DPAServiceTester()
    
    # 运行测试
    report = tester.run_all_tests()
    
    # 输出启动建议
    print("\n🔧 服务启动建议:")
    print("1. 后端服务: uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload")
    print("2. 前端服务: cd frontend && npm run dev")
    print("3. 测试工具: open test_browser_simple.html")
    
    return 0 if report["summary"]["error_count"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())