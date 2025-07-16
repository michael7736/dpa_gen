#!/usr/bin/env python3
"""
DPA系统管理脚本
"""

import sys
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path("/Users/mdwong001/Desktop/code/rag/DPA")
PYTHON_PATH = "/Users/mdwong001/mambaforge/envs/dpa_gen/bin/python"

class DPAManager:
    """DPA系统管理器"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.python_path = PYTHON_PATH
    
    def run_command(self, script_name: str, description: str = ""):
        """运行命令"""
        print(f"\n🚀 {description or script_name}")
        print("=" * 50)
        
        try:
            # 切换到项目目录
            original_cwd = Path.cwd()
            os.chdir(self.project_root)
            
            # 运行脚本
            result = subprocess.run([
                self.python_path, script_name
            ], cwd=self.project_root)
            
            # 恢复目录
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                print(f"✅ {description or script_name} 完成")
                return True
            else:
                print(f"❌ {description or script_name} 失败")
                return False
                
        except Exception as e:
            print(f"❌ 执行异常: {e}")
            return False
    
    def show_menu(self):
        """显示菜单"""
        print("\n🎛️  DPA系统管理器")
        print("=" * 50)
        print("1. 配置Neo4j数据库")
        print("2. 启动生产环境")
        print("3. 运行集成测试")
        print("4. 重启API服务")
        print("5. 查看服务状态")
        print("6. 查看日志")
        print("7. 停止所有服务")
        print("8. 完整系统部署")
        print("0. 退出")
    
    def configure_neo4j(self):
        """配置Neo4j"""
        return self.run_command("simple_neo4j_setup.py", "配置Neo4j数据库")
    
    def start_production(self):
        """启动生产环境"""
        return self.run_command("start_production.py", "启动生产环境")
    
    def run_integration_test(self):
        """运行集成测试"""
        return self.run_command("final_integration_test.py", "运行集成测试")
    
    def restart_api(self):
        """重启API服务"""
        return self.run_command("restart_api.py", "重启API服务")
    
    def show_status(self):
        """显示服务状态"""
        print("\n📊 服务状态检查")
        print("=" * 50)
        
        try:
            # 检查API进程
            result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"🟢 API服务运行中 (PID: {', '.join(pids)})")
            else:
                print("🔴 API服务未运行")
            
            # 检查端口
            result = subprocess.run(['lsof', '-i', ':8200'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("🟢 端口8200已占用")
            else:
                print("🔴 端口8200空闲")
            
            # 检查日志文件
            log_files = [
                "logs/api_production.log",
                "api_production.log",
                "api_8200.log"
            ]
            
            for log_file in log_files:
                log_path = self.project_root / log_file
                if log_path.exists():
                    size = log_path.stat().st_size
                    print(f"📄 日志文件: {log_file} ({size} bytes)")
            
            # 测试API响应
            try:
                import requests
                response = requests.get('http://localhost:8200/health', timeout=5)
                if response.status_code == 200:
                    health = response.json()
                    print(f"🟢 API健康状态: {health.get('status', 'unknown')}")
                else:
                    print(f"🔴 API健康检查失败: {response.status_code}")
            except Exception as e:
                print(f"🔴 API连接失败: {e}")
                
        except Exception as e:
            print(f"❌ 状态检查异常: {e}")
    
    def show_logs(self):
        """显示日志"""
        print("\n📄 日志查看")
        print("=" * 50)
        
        log_files = [
            "logs/api_production.log",
            "api_production.log",
            "api_8200.log"
        ]
        
        for log_file in log_files:
            log_path = self.project_root / log_file
            if log_path.exists():
                print(f"\n📋 {log_file} (最后20行):")
                try:
                    result = subprocess.run(['tail', '-n', '20', str(log_path)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(result.stdout)
                    else:
                        print("无法读取日志文件")
                except Exception as e:
                    print(f"读取日志失败: {e}")
                break
        else:
            print("未找到日志文件")
    
    def stop_services(self):
        """停止所有服务"""
        print("\n🛑 停止所有服务")
        print("=" * 50)
        
        try:
            # 停止uvicorn进程
            result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        try:
                            subprocess.run(['kill', pid])
                            print(f"✅ 终止进程: {pid}")
                        except Exception as e:
                            print(f"❌ 终止进程失败: {e}")
                            
                # 等待进程结束
                time.sleep(2)
                
                # 强制终止
                result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid.strip():
                            try:
                                subprocess.run(['kill', '-9', pid])
                                print(f"💀 强制终止进程: {pid}")
                            except Exception as e:
                                print(f"❌ 强制终止失败: {e}")
            else:
                print("ℹ️  没有找到运行的服务")
                
        except Exception as e:
            print(f"❌ 停止服务异常: {e}")
    
    def full_deployment(self):
        """完整系统部署"""
        print("\n🚀 完整系统部署")
        print("=" * 50)
        
        steps = [
            ("配置Neo4j数据库", self.configure_neo4j),
            ("启动生产环境", self.start_production),
            ("运行集成测试", self.run_integration_test),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 步骤: {step_name}")
            if not step_func():
                print(f"❌ 部署失败于: {step_name}")
                return False
            print(f"✅ 完成: {step_name}")
        
        print("\n🎉 完整系统部署成功!")
        return True
    
    def run(self):
        """运行管理器"""
        import os
        
        while True:
            self.show_menu()
            
            try:
                choice = input("\n请选择操作 (0-8): ").strip()
                
                if choice == "0":
                    print("👋 退出DPA管理器")
                    break
                elif choice == "1":
                    self.configure_neo4j()
                elif choice == "2":
                    self.start_production()
                elif choice == "3":
                    self.run_integration_test()
                elif choice == "4":
                    self.restart_api()
                elif choice == "5":
                    self.show_status()
                elif choice == "6":
                    self.show_logs()
                elif choice == "7":
                    self.stop_services()
                elif choice == "8":
                    self.full_deployment()
                else:
                    print("❌ 无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，退出管理器")
                break
            except Exception as e:
                print(f"❌ 操作异常: {e}")
            
            input("\n按回车键继续...")

def main():
    """主函数"""
    print("🎛️  DPA系统管理器启动")
    
    manager = DPAManager()
    manager.run()

if __name__ == "__main__":
    main()