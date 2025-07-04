"""
功能开关配置
用于控制不稳定功能的启用/禁用
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class FeatureFlag(BaseModel):
    """功能开关定义"""
    name: str
    enabled: bool = False
    description: str = ""
    rollout_percentage: float = Field(0.0, ge=0.0, le=100.0)  # 灰度发布百分比
    enabled_for_users: list[str] = Field(default_factory=list)  # 特定用户启用
    enabled_for_projects: list[str] = Field(default_factory=list)  # 特定项目启用
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureFlagManager:
    """功能开关管理器"""
    
    # 默认功能开关配置
    DEFAULT_FLAGS = {
        # 文档处理相关
        "use_improved_document_processor": FeatureFlag(
            name="use_improved_document_processor",
            enabled=False,
            description="使用改进版文档处理智能体",
            rollout_percentage=0.0,
            metadata={"version": "2.0"}
        ),
        "use_semantic_chunking": FeatureFlag(
            name="use_semantic_chunking",
            enabled=False,
            description="使用语义分块（实验性功能）",
            rollout_percentage=0.0
        ),
        "enable_ocr": FeatureFlag(
            name="enable_ocr",
            enabled=False,
            description="启用OCR文字识别",
            rollout_percentage=0.0
        ),
        "parallel_document_processing": FeatureFlag(
            name="parallel_document_processing",
            enabled=True,
            description="并行处理多个文档",
            rollout_percentage=100.0
        ),
        
        # AI功能相关
        "use_local_embeddings": FeatureFlag(
            name="use_local_embeddings",
            enabled=False,
            description="使用本地嵌入模型",
            rollout_percentage=0.0
        ),
        "enable_multi_modal": FeatureFlag(
            name="enable_multi_modal",
            enabled=False,
            description="启用多模态理解",
            rollout_percentage=0.0
        ),
        "smart_model_routing": FeatureFlag(
            name="smart_model_routing",
            enabled=True,
            description="智能模型路由（根据任务选择模型）",
            rollout_percentage=50.0
        ),
        
        # 记忆系统相关
        "enable_memory_system": FeatureFlag(
            name="enable_memory_system",
            enabled=False,
            description="启用项目记忆系统",
            rollout_percentage=0.0
        ),
        "use_knowledge_graph": FeatureFlag(
            name="use_knowledge_graph",
            enabled=False,
            description="使用知识图谱",
            rollout_percentage=0.0
        ),
        
        # 性能优化相关
        "enable_response_streaming": FeatureFlag(
            name="enable_response_streaming",
            enabled=True,
            description="启用流式响应",
            rollout_percentage=100.0
        ),
        "aggressive_caching": FeatureFlag(
            name="aggressive_caching",
            enabled=True,
            description="激进缓存策略",
            rollout_percentage=80.0
        ),
        "enable_request_batching": FeatureFlag(
            name="enable_request_batching",
            enabled=True,
            description="启用请求批处理",
            rollout_percentage=100.0
        ),
        
        # 安全相关
        "enable_pii_detection": FeatureFlag(
            name="enable_pii_detection",
            enabled=False,
            description="启用个人信息检测",
            rollout_percentage=0.0
        ),
        "strict_data_validation": FeatureFlag(
            name="strict_data_validation",
            enabled=True,
            description="严格数据验证",
            rollout_percentage=100.0
        ),
        
        # 实验性功能
        "enable_research_planner": FeatureFlag(
            name="enable_research_planner",
            enabled=False,
            description="启用研究规划智能体",
            rollout_percentage=0.0,
            metadata={"min_version": "0.5.0"}
        ),
        "enable_auto_summarization": FeatureFlag(
            name="enable_auto_summarization",
            enabled=False,
            description="启用自动摘要生成",
            rollout_percentage=10.0
        )
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """初始化功能开关管理器"""
        self.config_path = config_path or Path("config/feature_flags.json")
        self._flags = self.DEFAULT_FLAGS.copy()
        self._load_config()
        
    def _load_config(self):
        """从配置文件加载功能开关"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                for flag_name, flag_config in config.items():
                    if flag_name in self._flags:
                        # 更新现有标志
                        self._flags[flag_name] = FeatureFlag(**flag_config)
                    else:
                        # 添加新标志
                        self._flags[flag_name] = FeatureFlag(name=flag_name, **flag_config)
                        
                logger.info(f"Loaded {len(config)} feature flags from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load feature flags: {e}")
    
    def save_config(self):
        """保存功能开关配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                name: flag.dict(exclude={'created_at'})
                for name, flag in self._flags.items()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
                
            logger.info(f"Saved feature flags to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")
    
    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        check_rollout: bool = True
    ) -> bool:
        """
        检查功能是否启用
        
        Args:
            flag_name: 功能名称
            user_id: 用户ID（可选）
            project_id: 项目ID（可选）
            check_rollout: 是否检查灰度发布
            
        Returns:
            bool: 功能是否启用
        """
        if flag_name not in self._flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
            
        flag = self._flags[flag_name]
        
        # 全局禁用
        if not flag.enabled:
            return False
            
        # 检查特定用户
        if user_id and user_id in flag.enabled_for_users:
            return True
            
        # 检查特定项目
        if project_id and project_id in flag.enabled_for_projects:
            return True
            
        # 检查灰度发布
        if check_rollout and flag.rollout_percentage < 100.0:
            # 基于用户或项目ID的简单哈希来决定是否启用
            identifier = user_id or project_id or "default"
            hash_value = hash(identifier) % 100
            return hash_value < flag.rollout_percentage
            
        return True
    
    def enable_flag(self, flag_name: str, save: bool = True):
        """启用功能"""
        if flag_name in self._flags:
            self._flags[flag_name].enabled = True
            self._flags[flag_name].updated_at = datetime.now()
            if save:
                self.save_config()
            logger.info(f"Enabled feature flag: {flag_name}")
        else:
            logger.warning(f"Cannot enable unknown flag: {flag_name}")
    
    def disable_flag(self, flag_name: str, save: bool = True):
        """禁用功能"""
        if flag_name in self._flags:
            self._flags[flag_name].enabled = False
            self._flags[flag_name].updated_at = datetime.now()
            if save:
                self.save_config()
            logger.info(f"Disabled feature flag: {flag_name}")
        else:
            logger.warning(f"Cannot disable unknown flag: {flag_name}")
    
    def set_rollout_percentage(self, flag_name: str, percentage: float, save: bool = True):
        """设置灰度发布百分比"""
        if flag_name in self._flags:
            self._flags[flag_name].rollout_percentage = max(0.0, min(100.0, percentage))
            self._flags[flag_name].updated_at = datetime.now()
            if save:
                self.save_config()
            logger.info(f"Set rollout percentage for {flag_name}: {percentage}%")
        else:
            logger.warning(f"Cannot set rollout for unknown flag: {flag_name}")
    
    def enable_for_user(self, flag_name: str, user_id: str, save: bool = True):
        """为特定用户启用功能"""
        if flag_name in self._flags:
            if user_id not in self._flags[flag_name].enabled_for_users:
                self._flags[flag_name].enabled_for_users.append(user_id)
                self._flags[flag_name].updated_at = datetime.now()
                if save:
                    self.save_config()
                logger.info(f"Enabled {flag_name} for user: {user_id}")
        else:
            logger.warning(f"Cannot enable unknown flag: {flag_name}")
    
    def enable_for_project(self, flag_name: str, project_id: str, save: bool = True):
        """为特定项目启用功能"""
        if flag_name in self._flags:
            if project_id not in self._flags[flag_name].enabled_for_projects:
                self._flags[flag_name].enabled_for_projects.append(project_id)
                self._flags[flag_name].updated_at = datetime.now()
                if save:
                    self.save_config()
                logger.info(f"Enabled {flag_name} for project: {project_id}")
        else:
            logger.warning(f"Cannot enable unknown flag: {flag_name}")
    
    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """获取所有功能开关"""
        return self._flags.copy()
    
    def get_enabled_flags(self) -> list[str]:
        """获取所有启用的功能"""
        return [name for name, flag in self._flags.items() if flag.enabled]
    
    def get_flag_info(self, flag_name: str) -> Optional[FeatureFlag]:
        """获取功能开关详情"""
        return self._flags.get(flag_name)
    
    def create_flag(self, flag: FeatureFlag, save: bool = True):
        """创建新的功能开关"""
        if flag.name in self._flags:
            logger.warning(f"Feature flag already exists: {flag.name}")
            return
            
        self._flags[flag.name] = flag
        if save:
            self.save_config()
        logger.info(f"Created new feature flag: {flag.name}")


# 全局功能开关管理器实例
feature_flags = FeatureFlagManager()


# 便捷函数
def is_feature_enabled(
    flag_name: str,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> bool:
    """检查功能是否启用的便捷函数"""
    return feature_flags.is_enabled(flag_name, user_id, project_id)


# 装饰器：用于条件执行
def feature_flag(flag_name: str, fallback=None):
    """
    功能开关装饰器
    
    Usage:
        @feature_flag("enable_new_feature")
        def new_feature():
            return "new implementation"
            
        @feature_flag("enable_new_feature", fallback=old_feature)
        def new_feature():
            return "new implementation"
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从参数中提取user_id和project_id
            user_id = kwargs.get('user_id')
            project_id = kwargs.get('project_id')
            
            if is_feature_enabled(flag_name, user_id, project_id):
                return func(*args, **kwargs)
            elif fallback:
                return fallback(*args, **kwargs)
            else:
                raise RuntimeError(f"Feature '{flag_name}' is disabled and no fallback provided")
        
        # 保留原函数的元数据
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._feature_flag = flag_name
        
        return wrapper
    return decorator