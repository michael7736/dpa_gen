"""
WebSocket路由
处理实时连接和消息
"""

import json
import uuid
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...utils.logger import get_logger
from ..websocket import manager, get_progress_notifier

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    connection_id: str = Query(default_factory=lambda: str(uuid.uuid4())),
    db: Session = Depends(get_db_session)
):
    """
    WebSocket主端点
    支持实时进度推送和双向通信
    """
    try:
        # 验证用户身份（简化版本，生产环境需要更严格的验证）
        if not user_id:
            await websocket.close(code=4001, reason="Missing user ID")
            return
        
        # 建立连接
        await manager.connect(websocket, user_id, connection_id)
        
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    await handle_client_message(message, user_id, websocket, db)
                except json.JSONDecodeError:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }, websocket)
                except Exception as e:
                    logger.error(f"处理客户端消息失败: {e}")
                    await manager.send_personal_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)
        
        except WebSocketDisconnect:
            manager.disconnect(user_id, connection_id)
    
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
        manager.disconnect(user_id, connection_id)


async def handle_client_message(
    message: Dict[str, Any], 
    user_id: str, 
    websocket: WebSocket, 
    db: Session
):
    """处理客户端消息"""
    
    message_type = message.get("type")
    
    if message_type == "subscribe_pipeline":
        # 订阅管道进度
        pipeline_id = message.get("pipeline_id")
        if pipeline_id:
            manager.subscribe_pipeline(user_id, pipeline_id)
            
            # 发送当前状态
            notifier = get_progress_notifier()
            await notifier.notify_pipeline_progress(pipeline_id, db)
            
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "pipeline_id": pipeline_id
            }, websocket)
    
    elif message_type == "unsubscribe_pipeline":
        # 取消订阅管道
        pipeline_id = message.get("pipeline_id")
        if pipeline_id:
            manager.unsubscribe_pipeline(user_id, pipeline_id)
            await manager.send_personal_message({
                "type": "unsubscription_confirmed",
                "pipeline_id": pipeline_id
            }, websocket)
    
    elif message_type == "ping":
        # 心跳检测
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": message.get("timestamp")
        }, websocket)
    
    elif message_type == "get_status":
        # 获取连接状态
        await manager.send_personal_message({
            "type": "status",
            "user_id": user_id,
            "total_connections": manager.get_connection_count(),
            "user_connections": manager.get_user_connection_count(user_id),
            "subscriptions": list(manager.user_subscriptions.get(user_id, set()))
        }, websocket)
    
    else:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, websocket)


@router.get("/ws/stats")
async def get_websocket_stats():
    """获取WebSocket统计信息"""
    return {
        "total_connections": manager.get_connection_count(),
        "active_users": len(manager.active_connections),
        "total_subscriptions": sum(len(subs) for subs in manager.user_subscriptions.values()),
        "active_pipelines": len(manager.pipeline_subscribers)
    }