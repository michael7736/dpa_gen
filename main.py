#!/usr/bin/env python3
"""
DPA智能知识引擎 - 主启动文件
基于大语言模型的智能知识引擎系统
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from src.config.settings import get_settings
from src.utils.logger import setup_logging, get_logger


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="DPA智能知识引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                    # 启动开发服务器
  python main.py --env production   # 启动生产服务器
  python main.py --port 8080       # 指定端口
  python main.py --host 0.0.0.0    # 指定主机
        """
    )
    
    parser.add_argument(
        "--env",
        choices=["development", "production", "testing"],
        default="development",
        help="运行环境 (默认: development)"
    )
    
    parser.add_argument(
        "--host",
        default=None,
        help="服务器主机地址"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="服务器端口"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载 (仅开发环境)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数量 (仅生产环境)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default=None,
        help="日志级别"
    )
    
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="检查配置并退出"
    )
    
    return parser.parse_args()


def check_dependencies():
    """检查依赖项"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "langchain",
        "langgraph",
        "qdrant-client",
        "neo4j",
        "openai",
        "pydantic",
        "sqlalchemy",
        "asyncio"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    print("✅ 所有依赖项检查通过")


def check_configuration(settings):
    """检查配置"""
    print("📋 配置检查:")
    
    # 检查必要的配置项
    checks = [
        ("服务器配置", settings.server.host and settings.server.port),
        ("AI模型配置", settings.ai_model.openai_api_key),
        ("数据库配置", settings.database.postgresql_url),
        ("Qdrant配置", settings.qdrant.url),
        ("Neo4j配置", settings.neo4j.url),
    ]
    
    all_passed = True
    
    for check_name, condition in checks:
        if condition:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if not all_passed:
        print("\n❌ 配置检查失败，请检查环境变量和配置文件")
        return False
    
    print("✅ 配置检查通过")
    return True


def setup_environment(env: str):
    """设置环境"""
    # 设置环境变量
    os.environ["ENVIRONMENT"] = env
    
    # 根据环境设置默认值
    if env == "development":
        os.environ.setdefault("DEBUG", "true")
        os.environ.setdefault("LOG_LEVEL", "debug")
    elif env == "production":
        os.environ.setdefault("DEBUG", "false")
        os.environ.setdefault("LOG_LEVEL", "info")
    elif env == "testing":
        os.environ.setdefault("DEBUG", "true")
        os.environ.setdefault("LOG_LEVEL", "debug")
        os.environ.setdefault("TESTING", "true")


async def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置环境
    setup_environment(args.env)
    
    # 设置日志
    setup_logging(level=args.log_level)
    logger = get_logger(__name__)
    
    logger.info("🚀 启动DPA智能知识引擎...")
    logger.info(f"运行环境: {args.env}")
    
    # 检查依赖
    check_dependencies()
    
    # 加载配置
    try:
        settings = get_settings()
    except Exception as e:
        logger.error(f"❌ 配置加载失败: {e}")
        sys.exit(1)
    
    # 检查配置
    if args.check_config:
        if check_configuration(settings):
            print("✅ 配置检查完成")
            sys.exit(0)
        else:
            sys.exit(1)
    
    if not check_configuration(settings):
        sys.exit(1)
    
    # 确定服务器参数
    host = args.host or settings.server.host
    port = args.port or settings.server.port
    reload = args.reload or (args.env == "development" and settings.debug)
    log_level = args.log_level or ("debug" if settings.debug else "info")
    
    logger.info(f"服务器地址: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/docs")
    logger.info(f"自动重载: {'启用' if reload else '禁用'}")
    
    # 启动服务器
    try:
        if args.env == "production" and args.workers > 1:
            # 生产环境多进程模式
            logger.info(f"启动生产服务器 (工作进程: {args.workers})")
            uvicorn.run(
                "src.api.main:app",
                host=host,
                port=port,
                workers=args.workers,
                log_level=log_level,
                access_log=True,
                loop="uvloop" if os.name != "nt" else "asyncio"
            )
        else:
            # 开发/测试环境单进程模式
            logger.info("启动开发服务器")
            uvicorn.run(
                "src.api.main:app",
                host=host,
                port=port,
                reload=reload,
                log_level=log_level,
                access_log=True,
                reload_dirs=["src"] if reload else None
            )
            
    except KeyboardInterrupt:
        logger.info("👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 处理Windows下的事件循环策略
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主函数
    asyncio.run(main()) 