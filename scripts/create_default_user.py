"""创建默认用户脚本"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.postgresql import get_db_session
from src.models.user import User
from src.utils.logger import get_logger

logger = get_logger(__name__)

def create_default_user():
    """创建默认用户"""
    db = next(get_db_session())
    
    try:
        # 检查是否已存在
        existing = db.query(User).filter(User.email == "default@dpa.ai").first()
        if existing:
            logger.info(f"默认用户已存在: {existing.id}")
            return
        
        # 创建默认用户
        default_user = User(
            email="default@dpa.ai",
            username="default",
            full_name="Default User",
            is_active=True,
            is_superuser=False
        )
        
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        
        logger.info(f"默认用户创建成功: {default_user.id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建默认用户失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_default_user()