#!/usr/bin/env python3
"""
管理用户Neo4j实例的脚本
支持创建、启动、停止、删除用户专属的Neo4j容器
"""
import os
import sys
import argparse
import subprocess
import hashlib
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings

# 默认配置
DEFAULT_USER_ID = "u1"
BASE_BOLT_PORT = 7687
BASE_HTTP_PORT = 7474
TEMPLATE_FILE = Path(__file__).parent.parent / "docker" / "neo4j-user-template.yml"


def get_user_ports(user_id: str) -> tuple[int, int]:
    """根据用户ID生成端口号"""
    if user_id == DEFAULT_USER_ID:
        return BASE_BOLT_PORT, BASE_HTTP_PORT
    
    # 基于用户ID生成唯一端口
    user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16) % 1000
    bolt_port = BASE_BOLT_PORT + user_hash * 2
    http_port = BASE_HTTP_PORT + user_hash * 2
    
    return bolt_port, http_port


def get_user_password(user_id: str) -> str:
    """生成用户密码"""
    if user_id == DEFAULT_USER_ID:
        return settings.neo4j.password
    
    # 用户专属密码
    return f"{settings.neo4j.password}_{user_id}"


def create_user_compose_file(user_id: str, output_dir: Path) -> Path:
    """创建用户专属的docker-compose文件"""
    bolt_port, http_port = get_user_ports(user_id)
    password = get_user_password(user_id)
    
    # 读取模板
    with open(TEMPLATE_FILE, 'r') as f:
        template = f.read()
    
    # 替换变量
    content = template.replace("${USER_ID}", user_id)
    content = content.replace("${BOLT_PORT}", str(bolt_port))
    content = content.replace("${HTTP_PORT}", str(http_port))
    content = content.replace("${PASSWORD}", password)
    
    # 写入文件
    output_file = output_dir / f"docker-compose-neo4j-{user_id}.yml"
    with open(output_file, 'w') as f:
        f.write(content)
    
    return output_file


def ensure_network():
    """确保Docker网络存在"""
    try:
        subprocess.run(
            ["docker", "network", "create", "dpa_network"],
            capture_output=True,
            check=False
        )
    except Exception:
        pass


def create_instance(user_id: str):
    """创建用户Neo4j实例"""
    print(f"Creating Neo4j instance for user: {user_id}")
    
    # 确保网络存在
    ensure_network()
    
    # 创建compose文件
    output_dir = Path.cwd() / "docker" / "user_instances"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    compose_file = create_user_compose_file(user_id, output_dir)
    
    # 启动容器
    cmd = ["docker-compose", "-f", str(compose_file), "up", "-d"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        bolt_port, http_port = get_user_ports(user_id)
        print(f"✓ Neo4j instance created successfully")
        print(f"  Bolt URL: bolt://localhost:{bolt_port}")
        print(f"  Browser URL: http://localhost:{http_port}")
        print(f"  Username: neo4j")
        print(f"  Password: {get_user_password(user_id)}")
    else:
        print(f"✗ Failed to create instance: {result.stderr}")
        sys.exit(1)


def start_instance(user_id: str):
    """启动用户Neo4j实例"""
    print(f"Starting Neo4j instance for user: {user_id}")
    
    compose_file = Path.cwd() / "docker" / "user_instances" / f"docker-compose-neo4j-{user_id}.yml"
    
    if not compose_file.exists():
        print(f"✗ Compose file not found. Please create the instance first.")
        sys.exit(1)
    
    cmd = ["docker-compose", "-f", str(compose_file), "start"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Neo4j instance started successfully")
    else:
        print(f"✗ Failed to start instance: {result.stderr}")
        sys.exit(1)


def stop_instance(user_id: str):
    """停止用户Neo4j实例"""
    print(f"Stopping Neo4j instance for user: {user_id}")
    
    compose_file = Path.cwd() / "docker" / "user_instances" / f"docker-compose-neo4j-{user_id}.yml"
    
    if not compose_file.exists():
        print(f"✗ Compose file not found.")
        sys.exit(1)
    
    cmd = ["docker-compose", "-f", str(compose_file), "stop"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Neo4j instance stopped successfully")
    else:
        print(f"✗ Failed to stop instance: {result.stderr}")
        sys.exit(1)


def remove_instance(user_id: str, remove_volumes: bool = False):
    """删除用户Neo4j实例"""
    print(f"Removing Neo4j instance for user: {user_id}")
    
    compose_file = Path.cwd() / "docker" / "user_instances" / f"docker-compose-neo4j-{user_id}.yml"
    
    if not compose_file.exists():
        print(f"✗ Compose file not found.")
        sys.exit(1)
    
    # 停止并删除容器
    cmd = ["docker-compose", "-f", str(compose_file), "down"]
    if remove_volumes:
        cmd.append("-v")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # 删除compose文件
        compose_file.unlink()
        print(f"✓ Neo4j instance removed successfully")
        if remove_volumes:
            print(f"  Data volumes also removed")
    else:
        print(f"✗ Failed to remove instance: {result.stderr}")
        sys.exit(1)


def list_instances():
    """列出所有用户实例"""
    print("User Neo4j Instances:")
    print("-" * 60)
    
    # 列出所有运行的Neo4j容器
    cmd = ["docker", "ps", "-a", "--filter", "name=dpa_neo4j_", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"✗ Failed to list instances: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Manage user Neo4j instances")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new Neo4j instance")
    create_parser.add_argument("user_id", help="User ID")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a Neo4j instance")
    start_parser.add_argument("user_id", help="User ID")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a Neo4j instance")
    stop_parser.add_argument("user_id", help="User ID")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a Neo4j instance")
    remove_parser.add_argument("user_id", help="User ID")
    remove_parser.add_argument("--volumes", action="store_true", help="Also remove data volumes")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all Neo4j instances")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "create":
        create_instance(args.user_id)
    elif args.command == "start":
        start_instance(args.user_id)
    elif args.command == "stop":
        stop_instance(args.user_id)
    elif args.command == "remove":
        remove_instance(args.user_id, args.volumes)
    elif args.command == "list":
        list_instances()


if __name__ == "__main__":
    main()