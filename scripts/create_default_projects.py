#!/usr/bin/env python3
"""
为所有现有用户创建默认项目的脚本
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import and_

from src.database.postgresql import get_db_session, get_session_factory
from src.models.user import User
from src.models.project import Project, ProjectType, ProjectStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_default_project_for_user(session, user: User) -> Project:
    """为用户创建默认项目"""
    # 检查用户是否已有默认项目
    existing_default = session.query(Project).filter(
        and_(
            Project.user_id == user.id,
            Project.is_default == True
        )
    ).first()
    
    if existing_default:
        logger.info(f"用户 {user.username} 已有默认项目: {existing_default.name}")
        return existing_default
    
    # 创建默认项目
    default_project = Project(
        name=f"{user.username}的默认项目",
        description="系统自动创建的默认项目，用于存储所有文档和对话",
        user_id=user.id,
        is_default=True,
        type=ProjectType.CUSTOM,
        status=ProjectStatus.DRAFT,
        config={
            "auto_created": True,
            "creation_time": datetime.utcnow().isoformat()
        },
        context={
            "created_by": "system",
            "creation_method": "batch_default"
        }
    )
    
    session.add(default_project)
    session.commit()
    session.refresh(default_project)
    
    logger.info(f"为用户 {user.username} 创建默认项目: {default_project.name}")
    return default_project


def main():
    """主函数"""
    logger.info("开始为所有用户创建默认项目...")
    
    SessionLocal = get_session_factory()
    session = SessionLocal()
    
    try:
        # 获取所有用户
        users = session.query(User).all()
        
        logger.info(f"找到 {len(users)} 个用户")
        
        # 为每个用户创建默认项目
        for user in users:
            try:
                create_default_project_for_user(session, user)
            except Exception as e:
                logger.error(f"为用户 {user.username} 创建默认项目失败: {e}")
                session.rollback()
                continue
        
        logger.info("默认项目创建完成！")
    finally:
        session.close()


if __name__ == "__main__":
    main()