#!/usr/bin/env python3
"""
重启API服务的脚本
"""

import os
import time
import signal
import subprocess

def restart_api():
    """重启API服务"""
    print("🔄 重启API服务")
    print("=" * 40)
    
    # 1. 停止现有服务
    print("1️⃣ 停止现有服务...")
    try:
        # 查找uvicorn进程
        result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"   终止进程: {pid}")
                    os.kill(int(pid), signal.SIGTERM)
            
            # 等待进程结束
            time.sleep(3)
            
            # 强制终止如果还在运行
            result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"   强制终止进程: {pid}")
                        os.kill(int(pid), signal.SIGKILL)
        else:
            print("   没有找到运行的uvicorn进程")
            
    except Exception as e:
        print(f"   停止服务时出错: {e}")
    
    # 2. 启动新服务
    print("\n2️⃣ 启动新服务...")
    try:
        # 切换到项目目录
        os.chdir('/Users/mdwong001/Desktop/code/rag/DPA')
        
        # 启动服务（无重载模式）
        cmd = [
            '/Users/mdwong001/mambaforge/envs/dpa_gen/bin/python',
            '-m', 'uvicorn',
            'src.api.main:app',
            '--host', '0.0.0.0',
            '--port', '8200',
            '--log-level', 'info'
        ]
        
        # 后台启动
        with open('api_production.log', 'w') as f:
            process = subprocess.Popen(cmd, stdout=f, stderr=f)
            
        print(f"   ✅ 服务已启动 (PID: {process.pid})")
        print(f"   📄 日志文件: api_production.log")
        
        # 等待服务启动
        print("\n3️⃣ 等待服务启动...")
        time.sleep(5)
        
        # 验证服务状态
        try:
            import requests
            response = requests.get('http://localhost:8200/health', timeout=10)
            if response.status_code == 200:
                health = response.json()
                print(f"   ✅ 服务健康: {health['status']}")
            else:
                print(f"   ❌ 服务不健康: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 健康检查失败: {e}")
            
    except Exception as e:
        print(f"   启动服务时出错: {e}")

if __name__ == "__main__":
    restart_api()