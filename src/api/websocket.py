"""
WebSocket支持模块
提供实时进度推送功能
"""

import json
import asyncio
from typing import Dict, Set, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..utils.logger import get_logger
from ..models.processing_pipeline import ProcessingPipeline, PipelineStage
from ..database.postgresql import get_db_session

logger = get_logger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储所有活跃连接 {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 存储用户订阅的管道 {user_id: {pipeline_id}}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # 存储管道的订阅者 {pipeline_id: {user_id}}
        self.pipeline_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """接受新的WebSocket连接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][connection_id] = websocket
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        logger.info(f"WebSocket连接建立: user={user_id}, connection={connection_id}")
        
        # 发送连接确认消息
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, user_id: str, connection_id: str):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(connection_id, None)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # 清理订阅
        if user_id in self.user_subscriptions:
            for pipeline_id in self.user_subscriptions[user_id].copy():
                self.unsubscribe_pipeline(user_id, pipeline_id)
        
        logger.info(f"WebSocket连接断开: user={user_id}, connection={connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")
    
    async def send_user_message(self, message: Dict[str, Any], user_id: str):
        """发送用户消息（所有连接）"""
        if user_id in self.active_connections:
            disconnected_connections = []
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"发送用户消息失败: user={user_id}, connection={connection_id}, error={e}")
                    disconnected_connections.append(connection_id)
            
            # 清理断开的连接
            for connection_id in disconnected_connections:
                self.disconnect(user_id, connection_id)
    
    async def broadcast_pipeline_update(self, pipeline_id: str, message: Dict[str, Any]):
        """广播管道更新消息"""
        if pipeline_id in self.pipeline_subscribers:
            for user_id in self.pipeline_subscribers[pipeline_id].copy():
                await self.send_user_message(message, user_id)
    
    def subscribe_pipeline(self, user_id: str, pipeline_id: str):
        """订阅管道更新"""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(pipeline_id)
        
        if pipeline_id not in self.pipeline_subscribers:
            self.pipeline_subscribers[pipeline_id] = set()
        self.pipeline_subscribers[pipeline_id].add(user_id)
        
        logger.info(f"用户订阅管道: user={user_id}, pipeline={pipeline_id}")
    
    def unsubscribe_pipeline(self, user_id: str, pipeline_id: str):
        """取消订阅管道"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(pipeline_id)
        
        if pipeline_id in self.pipeline_subscribers:
            self.pipeline_subscribers[pipeline_id].discard(user_id)
            if not self.pipeline_subscribers[pipeline_id]:
                del self.pipeline_subscribers[pipeline_id]
        
        logger.info(f"用户取消订阅管道: user={user_id}, pipeline={pipeline_id}")
    
    def get_connection_count(self) -> int:
        """获取总连接数"""
        total = 0
        for user_connections in self.active_connections.values():
            total += len(user_connections)
        return total
    
    def get_user_connection_count(self, user_id: str) -> int:
        """获取用户连接数"""
        return len(self.active_connections.get(user_id, {}))


# 全局连接管理器实例
manager = ConnectionManager()


class ProgressNotifier:
    """进度通知器"""
    
    @staticmethod
    async def notify_pipeline_progress(pipeline_id: str, db: Session):
        """通知管道进度更新"""
        try:
            # 获取管道信息
            pipeline = db.query(ProcessingPipeline).filter(
                ProcessingPipeline.id == pipeline_id
            ).first()
            
            if not pipeline:
                return
            
            # 获取所有阶段
            stages = db.query(PipelineStage).filter(
                PipelineStage.pipeline_id == pipeline.id
            ).order_by(PipelineStage.id).all()
            
            # 构建进度消息
            stage_data = []
            for stage in stages:
                stage_info = {
                    "id": stage.stage_type,
                    "name": stage.stage_name,
                    "status": stage.status,
                    "progress": stage.progress,
                    "message": stage.message,
                    "can_interrupt": stage.can_interrupt,
                    "started_at": stage.started_at.isoformat() if stage.started_at else None,
                    "completed_at": stage.completed_at.isoformat() if stage.completed_at else None,
                    "duration": stage.duration,
                    "error": stage.error
                }
                stage_data.append(stage_info)
            
            message = {
                "type": "pipeline_progress",
                "pipeline_id": str(pipeline.id),
                "document_id": str(pipeline.document_id),
                "overall_progress": pipeline.overall_progress,
                "current_stage": pipeline.current_stage,
                "stages": stage_data,
                "can_resume": pipeline.can_resume,
                "interrupted": pipeline.interrupted,
                "completed": pipeline.completed,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 广播更新
            await manager.broadcast_pipeline_update(str(pipeline.id), message)
            
        except Exception as e:
            logger.error(f"通知管道进度失败: {e}")
    
    @staticmethod
    async def notify_stage_update(stage_id: str, db: Session):
        """通知阶段更新"""
        try:
            stage = db.query(PipelineStage).filter(
                PipelineStage.id == stage_id
            ).first()
            
            if not stage:
                return
            
            message = {
                "type": "stage_update",
                "pipeline_id": str(stage.pipeline_id),
                "stage_id": str(stage.id),
                "stage_type": stage.stage_type,
                "stage_name": stage.stage_name,
                "status": stage.status,
                "progress": stage.progress,
                "message": stage.message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast_pipeline_update(str(stage.pipeline_id), message)
            
        except Exception as e:
            logger.error(f"通知阶段更新失败: {e}")


# 获取进度通知器实例
def get_progress_notifier() -> ProgressNotifier:
    return ProgressNotifier()