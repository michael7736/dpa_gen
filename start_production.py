#!/usr/bin/env python3
"""
生产环境启动脚本
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# 设置项目路径
PROJECT_ROOT = Path("/Users/mdwong001/Desktop/code/rag/DPA")
PYTHON_PATH = "/Users/mdwong001/mambaforge/envs/dpa_gen/bin/python"
LOG_DIR = PROJECT_ROOT / "logs"

def setup_directories():
    """创建必要的目录"""
    print("📁 创建必要目录...")
    
    # 创建日志目录
    LOG_DIR.mkdir(exist_ok=True)
    print(f"   ✅ 日志目录: {LOG_DIR}")
    
    # 创建数据目录
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"   ✅ 数据目录: {data_dir}")

def check_dependencies():
    """检查依赖项"""
    print("\n🔍 检查依赖项...")
    
    # 检查Python环境
    result = subprocess.run([PYTHON_PATH, "--version"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ Python: {result.stdout.strip()}")
    else:
        print(f"   ❌ Python环境问题")
        return False
    
    # 检查关键包
    packages = ["fastapi", "uvicorn", "neo4j", "qdrant-client", "sqlalchemy"]
    for pkg in packages:
        result = subprocess.run([PYTHON_PATH, "-c", f"import {pkg}; print('{pkg} OK')"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {pkg}: 已安装")
        else:
            print(f"   ❌ {pkg}: 未安装或有问题")
            return False
    
    return True

def setup_neo4j():
    """设置Neo4j（简化版）"""
    print("\n🔧 设置Neo4j...")
    
    try:
        # 执行Neo4j设置
        os.chdir(PROJECT_ROOT)
        result = subprocess.run([
            PYTHON_PATH, "-c", """
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
import os
try:
    from neo4j import GraphDatabase
    url = os.getenv('NEO4J_URL', 'bolt://rtx4080:7687')
    user = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', '1234qwer')
    driver = GraphDatabase.driver(url, auth=(user, password))
    with driver.session() as session:
        session.run('RETURN 1')
    driver.close()
    print('Neo4j连接成功')
except Exception as e:
    print(f'Neo4j连接失败: {e}')
    sys.exit(1)
"""
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
            return True
        else:
            print(f"   ⚠️  Neo4j问题: {result.stderr.strip()}")
            print("   继续启动（Neo4j可选）")
            return True
            
    except Exception as e:
        print(f"   ⚠️  Neo4j设置异常: {e}")
        return True

def stop_existing_services():
    """停止现有服务"""
    print("\n🛑 停止现有服务...")
    
    try:
        # 查找并停止uvicorn进程
        result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    print(f"   🔄 终止进程: {pid}")
                    os.kill(int(pid), signal.SIGTERM)
            
            # 等待进程结束
            time.sleep(3)
            
            # 检查是否还在运行
            result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        print(f"   💀 强制终止: {pid}")
                        os.kill(int(pid), signal.SIGKILL)
        else:
            print("   ℹ️  没有找到运行的服务")
            
    except Exception as e:
        print(f"   ⚠️  停止服务时出错: {e}")

def start_api_service():
    """启动API服务"""
    print("\n🚀 启动API服务...")
    
    try:
        # 切换到项目目录
        os.chdir(PROJECT_ROOT)
        
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        
        # 启动命令
        cmd = [
            PYTHON_PATH,
            '-m', 'uvicorn',
            'src.api.main:app',
            '--host', '0.0.0.0',
            '--port', '8200',
            '--log-level', 'info',
            '--workers', '1'  # 单进程模式
        ]
        
        # 日志文件
        log_file = LOG_DIR / "api_production.log"
        
        print(f"   📋 启动命令: {' '.join(cmd)}")
        print(f"   📄 日志文件: {log_file}")
        
        # 启动服务
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=PROJECT_ROOT
            )
        
        print(f"   ✅ 服务已启动 (PID: {process.pid})")
        
        # 等待服务启动
        print("   ⏳ 等待服务启动...")
        time.sleep(8)
        
        # 验证服务状态
        try:
            import requests
            response = requests.get('http://localhost:8200/health', timeout=10)
            if response.status_code == 200:
                health = response.json()
                print(f"   ✅ 服务健康: {health.get('status', 'unknown')}")
                return True
            else:
                print(f"   ❌ 服务不健康: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 健康检查失败: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ 启动服务失败: {e}")
        return False

def show_status():
    """显示服务状态"""
    print("\n📊 服务状态")
    print("=" * 50)
    
    try:
        # 检查进程
        result = subprocess.run(['pgrep', '-f', 'uvicorn.*8200'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"🟢 API服务运行中")
            for pid in pids:
                if pid.strip():
                    print(f"   PID: {pid}")
        else:
            print("🔴 API服务未运行")
        
        # 检查端口
        result = subprocess.run(['lsof', '-i', ':8200'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"🟢 端口8200被占用")
        else:
            print("🔴 端口8200空闲")
            
        # 检查日志文件
        log_file = LOG_DIR / "api_production.log"
        if log_file.exists():
            size = log_file.stat().st_size
            print(f"📄 日志文件: {log_file} ({size} bytes)")
        
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")

def main():
    """主函数"""
    print("🚀 DPA生产环境启动器")
    print("=" * 50)
    
    # 1. 设置目录
    setup_directories()
    
    # 2. 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败")
        sys.exit(1)
    
    # 3. 设置Neo4j
    if not setup_neo4j():
        print("❌ Neo4j设置失败")
        sys.exit(1)
    
    # 4. 停止现有服务
    stop_existing_services()
    
    # 5. 启动API服务
    if not start_api_service():
        print("❌ API服务启动失败")
        sys.exit(1)
    
    # 6. 显示状态
    show_status()
    
    print("\n🎉 生产环境启动完成!")
    print("\n📋 访问信息:")
    print("   API服务: http://localhost:8200")
    print("   健康检查: http://localhost:8200/health")
    print("   API文档: http://localhost:8200/docs")
    
    print("\n📄 日志监控:")
    print(f"   tail -f {LOG_DIR}/api_production.log")
    
    print("\n🔧 管理命令:")
    print("   停止服务: pkill -f 'uvicorn.*8200'")
    print("   重启服务: python start_production.py")

if __name__ == "__main__":
    main()