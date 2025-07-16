"""
MVP认知状态定义 - 支持多用户隔离预埋
单用户阶段使用默认值，为未来多用户完全隔离做准备
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

# 默认用户ID（单用户阶段）
DEFAULT_USER_ID = "u1"


class MVPCognitiveState(TypedDict):
    """
    MVP版认知状态 - 最小可行集
    包含用户隔离预埋
    """
    
    # 基础交互
    messages: Annotated[List[BaseMessage], add_messages]
    thread_id: str
    
    # 用户和项目标识（为多用户预埋）
    user_id: str  # 默认 "u1"
    project_id: Optional[str]
    
    # 简化的记忆层（单用户阶段不需要user_id过滤）
    working_memory: Dict[str, Any]      # 最多20项
    recent_documents: List[Dict]        # 最近10个文档
    
    # 处理状态
    current_chunk: Optional[Dict[str, Any]]    # 当前处理的文本块
    query_result: Optional[Dict[str, Any]]     # 查询结果
    
    # Memory Bank快照（路径会包含user_id）
    memory_bank_snapshot: Optional[Dict[str, Any]]
    
    # 控制和错误处理
    last_error: Optional[str]
    processing_status: str  # "idle", "processing", "completed", "failed"
    created_at: datetime
    updated_at: datetime


def create_initial_state(
    user_id: str = DEFAULT_USER_ID,
    project_id: Optional[str] = None,
    thread_id: Optional[str] = None
) -> MVPCognitiveState:
    """
    创建初始状态
    
    Args:
        user_id: 用户ID（默认"u1"）
        project_id: 项目ID
        thread_id: 会话ID
        
    Returns:
        初始化的认知状态
    """
    import uuid
    
    return MVPCognitiveState(
        messages=[],
        thread_id=thread_id or str(uuid.uuid4()),
        user_id=user_id,
        project_id=project_id,
        working_memory={},
        recent_documents=[],
        current_chunk=None,
        query_result=None,
        memory_bank_snapshot=None,
        last_error=None,
        processing_status="idle",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class WorkingMemoryManager:
    """工作记忆管理器 - 控制容量和访问"""
    
    MAX_ITEMS = 20  # 工作记忆最大项数
    
    @staticmethod
    def add_item(
        state: MVPCognitiveState,
        key: str,
        value: Any,
        priority: int = 0
    ) -> MVPCognitiveState:
        """添加项到工作记忆"""
        working_memory = state["working_memory"].copy()
        
        # 添加时间戳和优先级
        working_memory[key] = {
            "value": value,
            "priority": priority,
            "accessed_at": datetime.now().isoformat(),
            "access_count": 1
        }
        
        # 如果超过容量，移除最少访问的项
        if len(working_memory) > WorkingMemoryManager.MAX_ITEMS:
            # 按访问次数和时间排序
            sorted_keys = sorted(
                working_memory.keys(),
                key=lambda k: (
                    working_memory[k]["access_count"],
                    working_memory[k]["accessed_at"]
                )
            )
            # 移除最少访问的项
            for key_to_remove in sorted_keys[:len(working_memory) - WorkingMemoryManager.MAX_ITEMS]:
                del working_memory[key_to_remove]
                
        state["working_memory"] = working_memory
        state["updated_at"] = datetime.now()
        return state
        
    @staticmethod
    def get_item(
        state: MVPCognitiveState,
        key: str
    ) -> Optional[Any]:
        """从工作记忆获取项"""
        if key in state["working_memory"]:
            # 更新访问信息
            item = state["working_memory"][key]
            item["accessed_at"] = datetime.now().isoformat()
            item["access_count"] += 1
            return item["value"]
        return None
        
    @staticmethod
    def get_all_items(state: MVPCognitiveState) -> Dict[str, Any]:
        """获取所有工作记忆项（仅值）"""
        return {
            key: item["value"]
            for key, item in state["working_memory"].items()
        }


class StateValidator:
    """状态验证器 - 确保状态一致性"""
    
    @staticmethod
    def validate_state(state: MVPCognitiveState) -> bool:
        """验证状态是否有效"""
        # 检查必需字段
        required_fields = ["messages", "thread_id", "user_id"]
        for field in required_fields:
            if field not in state:
                return False
                
        # 检查工作记忆容量
        if len(state.get("working_memory", {})) > WorkingMemoryManager.MAX_ITEMS:
            return False
            
        # 检查文档数量
        if len(state.get("recent_documents", [])) > 10:
            return False
            
        return True
        
    @staticmethod
    def sanitize_state(state: MVPCognitiveState) -> MVPCognitiveState:
        """清理和修复状态"""
        # 确保所有必需字段存在
        if "user_id" not in state:
            state["user_id"] = DEFAULT_USER_ID
            
        if "project_id" not in state:
            state["project_id"] = None
            
        # 限制集合大小
        if len(state.get("working_memory", {})) > WorkingMemoryManager.MAX_ITEMS:
            # 保留最近访问的项
            sorted_items = sorted(
                state["working_memory"].items(),
                key=lambda x: x[1].get("accessed_at", ""),
                reverse=True
            )
            state["working_memory"] = dict(sorted_items[:WorkingMemoryManager.MAX_ITEMS])
            
        if len(state.get("recent_documents", [])) > 10:
            state["recent_documents"] = state["recent_documents"][-10:]
            
        state["updated_at"] = datetime.now()
        return state


def get_namespace_for_state(state: MVPCognitiveState) -> str:
    """
    获取状态的命名空间
    单用户阶段：返回 project_id 或 "default"
    多用户阶段：返回 "{user_id}/{project_id}"
    """
    user_id = state.get("user_id", DEFAULT_USER_ID)
    project_id = state.get("project_id", "default")
    
    if user_id == DEFAULT_USER_ID:
        # 单用户阶段，简化命名空间
        return project_id
    else:
        # 多用户阶段，包含用户ID
        return f"{user_id}/{project_id}"


def filter_state_for_user(state: MVPCognitiveState, user_id: str) -> MVPCognitiveState:
    """
    过滤状态数据，只返回属于指定用户的内容
    单用户阶段：直接返回所有内容
    多用户阶段：过滤数据
    """
    if user_id == DEFAULT_USER_ID or state.get("user_id") == user_id:
        # 单用户阶段或用户匹配，返回完整状态
        return state
    else:
        # 多用户阶段，返回空状态
        return create_initial_state(user_id=user_id)