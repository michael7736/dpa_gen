#!/usr/bin/env python3
"""
启动DPA服务的Python脚本
"""
import subprocess
import sys
import time
import os
import signal
import requests
from pathlib import Path

def start_backend():
    """启动后端服务"""
    print("🔧 启动后端服务...")
    
    # 使用conda环境的Python路径
    python_path = "/Users/mdwong001/miniconda3/envs/dpa_gen/bin/python"
    
    cmd = [
        python_path, "-m", "uvicorn", 
        "src.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8200", 
        "--reload"
    ]
    
    try:
        # 启动后端服务
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ 后端服务已启动 (PID: {process.pid})")
        
        # 保存PID
        with open("backend.pid", "w") as f:
            f.write(str(process.pid))
        
        # 等待服务启动
        print("⏳ 等待后端服务启动...")
        for i in range(30):
            try:
                response = requests.get("http://localhost:8200/api/v1/health", timeout=5)
                if response.status_code == 200:
                    print("✅ 后端服务已就绪")
                    return process
            except:
                pass
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ 后端服务启动超时")
        return None
        
    except Exception as e:
        print(f"❌ 启动后端服务失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("\n🎨 启动前端服务...")
    
    # 切换到前端目录
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ 前端目录不存在")
        return None
    
    # 检查package.json
    if not (frontend_dir / "package.json").exists():
        print("❌ 未找到package.json")
        return None
    
    # 检查node_modules
    if not (frontend_dir / "node_modules").exists():
        print("📦 安装前端依赖...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("✅ 前端依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 前端依赖安装失败")
            return None
    
    # 启动前端服务
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ 前端服务已启动 (PID: {process.pid})")
        
        # 保存PID
        with open("frontend.pid", "w") as f:
            f.write(str(process.pid))
        
        # 等待服务启动
        print("⏳ 等待前端服务启动...")
        for i in range(60):
            try:
                response = requests.get("http://localhost:8230", timeout=5)
                if response.status_code == 200:
                    print("✅ 前端服务已就绪")
                    return process
            except:
                pass
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ 前端服务启动超时")
        return None
        
    except Exception as e:
        print(f"❌ 启动前端服务失败: {e}")
        return None

def verify_services():
    """验证服务状态"""
    print("\n🔍 验证服务状态...")
    
    # 检查后端
    try:
        response = requests.get("http://localhost:8200/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务: 正常")
            backend_ok = True
        else:
            print("❌ 后端服务: 异常")
            backend_ok = False
    except:
        print("❌ 后端服务: 无法连接")
        backend_ok = False
    
    # 检查前端
    try:
        response = requests.get("http://localhost:8230", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务: 正常")
            frontend_ok = True
        else:
            print("❌ 前端服务: 异常")
            frontend_ok = False
    except:
        print("❌ 前端服务: 无法连接")
        frontend_ok = False
    
    return backend_ok and frontend_ok

def cleanup_handler(signum, frame):
    """清理处理器"""
    print("\n🛑 停止DPA服务...")
    
    # 停止后端
    if os.path.exists("backend.pid"):
        try:
            with open("backend.pid", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            os.remove("backend.pid")
            print("✅ 后端服务已停止")
        except:
            pass
    
    # 停止前端
    if os.path.exists("frontend.pid"):
        try:
            with open("frontend.pid", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            os.remove("frontend.pid")
            print("✅ 前端服务已停止")
        except:
            pass
    
    sys.exit(0)

def main():
    """主函数"""
    print("🚀 DPA服务启动脚本")
    print("=" * 30)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # 启动后端服务
    backend_process = start_backend()
    if not backend_process:
        print("❌ 后端服务启动失败")
        return 1
    
    # 启动前端服务  
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ 前端服务启动失败")
        return 1
    
    # 验证服务
    if verify_services():
        print("\n🎉 DPA服务启动成功！")
        print("=" * 30)
        print("\n📊 服务信息:")
        print("   后端服务: http://localhost:8200")
        print("   API文档:  http://localhost:8200/docs")
        print("   前端服务: http://localhost:8230")
        print("   AAG页面:  http://localhost:8230/aag")
        print("\n🔍 测试工具:")
        print("   浏览器测试: open test_browser_simple.html")
        print("   WebSocket诊断: open websocket_diagnostic.html")
        print("\n🛑 停止服务: Ctrl+C")
        print("\n🎯 现在可以开始使用DPA了！")
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            cleanup_handler(None, None)
    else:
        print("\n❌ 服务验证失败")
        cleanup_handler(None, None)
        return 1

if __name__ == "__main__":
    sys.exit(main())