#!/usr/bin/env python3
"""
DPA服务状态检查脚本
快速检查和启动DPA服务
"""

import subprocess
import sys
import time
import requests
import json
import os
from pathlib import Path

def check_command_exists(command):
    """检查命令是否存在"""
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_port_occupied(port):
    """检查端口是否被占用"""
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip()
    except FileNotFoundError:
        # 如果没有lsof命令，尝试netstat
        try:
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            return f':{port}' in result.stdout
        except FileNotFoundError:
            return False

def check_service_health(url, timeout=5):
    """检查服务健康状态"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def kill_process_by_port(port):
    """通过端口杀死进程"""
    try:
        # 查找占用端口的进程
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"✅ 已杀死占用端口{port}的进程 (PID: {pid})")
                except subprocess.CalledProcessError:
                    print(f"❌ 无法杀死进程 (PID: {pid})")
        return True
    except FileNotFoundError:
        print("❌ 缺少lsof命令，无法自动杀死进程")
        return False

def start_backend():
    """启动后端服务"""
    print("🔧 启动后端服务...")
    
    # 检查主文件是否存在
    if not os.path.exists('src/api/main.py'):
        print("❌ 未找到后端主文件 src/api/main.py")
        return False
    
    # 检查端口
    if check_port_occupied(8200):
        print("⚠️ 端口8200已被占用")
        response = input("是否杀死占用进程？(y/n): ")
        if response.lower() == 'y':
            kill_process_by_port(8200)
        else:
            print("❌ 无法启动后端服务")
            return False
    
    # 启动服务
    try:
        process = subprocess.Popen(
            ['uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', '8200', '--reload'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        print("⏳ 等待后端服务启动...")
        for i in range(30):
            if check_service_health('http://localhost:8200/api/v1/health'):
                print("✅ 后端服务启动成功")
                return True
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ 后端服务启动超时")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ 启动后端服务时出错: {e}")
        return False

def start_frontend():
    """启动前端服务"""
    print("🎨 启动前端服务...")
    
    # 检查package.json是否存在
    if not os.path.exists('frontend/package.json'):
        print("❌ 未找到前端配置文件 frontend/package.json")
        return False
    
    # 检查端口
    if check_port_occupied(8230):
        print("⚠️ 端口8230已被占用")
        response = input("是否杀死占用进程？(y/n): ")
        if response.lower() == 'y':
            kill_process_by_port(8230)
        else:
            print("❌ 无法启动前端服务")
            return False
    
    # 检查依赖
    if not os.path.exists('frontend/node_modules'):
        print("📦 安装前端依赖...")
        try:
            subprocess.run(['npm', 'install'], cwd='frontend', check=True)
            print("✅ 前端依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 前端依赖安装失败")
            return False
    
    # 启动服务
    try:
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd='frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        print("⏳ 等待前端服务启动...")
        for i in range(60):
            if check_service_health('http://localhost:8230'):
                print("✅ 前端服务启动成功")
                return True
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ 前端服务启动超时")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ 启动前端服务时出错: {e}")
        return False

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    issues = []
    
    # 检查Python
    if not check_command_exists('python'):
        issues.append("Python未安装或未配置")
    
    # 检查Node.js
    if not check_command_exists('node'):
        issues.append("Node.js未安装")
    
    # 检查npm
    if not check_command_exists('npm'):
        issues.append("npm未安装")
    
    # 检查uvicorn
    if not check_command_exists('uvicorn'):
        issues.append("uvicorn未安装")
    
    # 检查conda环境
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'dpa_gen':
        issues.append(f"当前conda环境: {conda_env}, 需要: dpa_gen")
    
    if issues:
        print("❌ 环境配置问题:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ 环境配置正常")
        return True

def check_services():
    """检查服务状态"""
    print("\n🔍 检查服务状态...")
    
    # 检查后端服务
    backend_ok = check_service_health('http://localhost:8200/api/v1/health')
    if backend_ok:
        print("✅ 后端服务: 正常运行")
    else:
        print("❌ 后端服务: 未运行")
    
    # 检查前端服务
    frontend_ok = check_service_health('http://localhost:8230')
    if frontend_ok:
        print("✅ 前端服务: 正常运行")
    else:
        print("❌ 前端服务: 未运行")
    
    return backend_ok, frontend_ok

def main():
    """主函数"""
    print("🚀 DPA服务状态检查和启动工具")
    print("=" * 40)
    
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # 检查环境
    if not check_environment():
        print("\n💡 解决方案:")
        print("1. 激活conda环境: conda activate dpa_gen")
        print("2. 安装uvicorn: pip install uvicorn")
        print("3. 检查Node.js安装: node --version")
        return 1
    
    # 检查服务状态
    backend_ok, frontend_ok = check_services()
    
    if backend_ok and frontend_ok:
        print("\n🎉 所有服务正常运行!")
        print_service_info()
        return 0
    
    # 询问是否启动服务
    if not backend_ok:
        response = input("\n🔧 是否启动后端服务？(y/n): ")
        if response.lower() == 'y':
            start_backend()
    
    if not frontend_ok:
        response = input("\n🎨 是否启动前端服务？(y/n): ")
        if response.lower() == 'y':
            start_frontend()
    
    # 再次检查服务状态
    print("\n🔍 再次检查服务状态...")
    backend_ok, frontend_ok = check_services()
    
    if backend_ok and frontend_ok:
        print("\n🎉 所有服务启动成功!")
        print_service_info()
        return 0
    else:
        print("\n❌ 部分服务启动失败")
        return 1

def print_service_info():
    """打印服务信息"""
    print("\n📊 服务信息:")
    print("   后端服务: http://localhost:8200")
    print("   API文档:  http://localhost:8200/docs")
    print("   前端服务: http://localhost:8230")
    print("   AAG页面:  http://localhost:8230/aag")
    print("\n🔍 测试工具:")
    print("   浏览器测试: open test_browser_simple.html")
    print("   WebSocket诊断: open websocket_diagnostic.html")
    print("   Python测试: python test_services.py")

if __name__ == "__main__":
    sys.exit(main())