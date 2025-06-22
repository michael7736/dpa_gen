"""
健康检查API路由
提供系统健康状态和性能监控接口
"""

import asyncio
import psutil
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...database.qdrant_client import get_qdrant_manager
from ...database.neo4j_client import get_neo4j_manager
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthStatus(BaseModel):
    """健康状态响应"""
    status: str
    timestamp: str
    services: Dict[str, str]
    system_info: Dict[str, Any]
    version: str


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    系统健康检查
    
    Returns:
        系统健康状态信息
    """
    try:
        # 检查各个服务状态
        services_status = await check_services_health()
        
        # 获取系统信息
        system_info = get_system_info()
        
        # 确定整体状态
        overall_status = "healthy"
        for service, status in services_status.items():
            if status != "healthy":
                overall_status = "degraded"
                break
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            services=services_status,
            system_info=system_info,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            services={},
            system_info={},
            version="1.0.0"
        )


async def check_services_health() -> Dict[str, str]:
    """检查各个服务的健康状态"""
    services_status = {}
    
    # 检查Qdrant
    try:
        qdrant_manager = get_qdrant_manager()
        await qdrant_manager.collection_exists("test")
        services_status["qdrant"] = "healthy"
    except Exception as e:
        logger.warning(f"Qdrant健康检查失败: {e}")
        services_status["qdrant"] = "unhealthy"
    
    # 检查Neo4j
    try:
        neo4j_manager = get_neo4j_manager()
        await neo4j_manager.execute_query("RETURN 1")
        services_status["neo4j"] = "healthy"
    except Exception as e:
        logger.warning(f"Neo4j健康检查失败: {e}")
        services_status["neo4j"] = "unhealthy"
    
    # API服务本身
    services_status["api"] = "healthy"
    
    return services_status


def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": memory_info,
            "disk": disk_info,
            "uptime": get_uptime()
        }
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return {}


def get_uptime() -> str:
    """获取系统运行时间"""
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}天 {hours}小时 {minutes}分钟"
        
    except Exception:
        return "未知"


@router.get("/health/services")
async def services_health():
    """
    获取各个服务的详细健康状态
    
    Returns:
        各服务的详细状态信息
    """
    try:
        services_detail = {}
        
        # Qdrant详细状态
        try:
            qdrant_manager = get_qdrant_manager()
            collections = ["documents", "chunks", "entities"]
            qdrant_detail = {
                "status": "healthy",
                "collections": {}
            }
            
            for collection in collections:
                try:
                    exists = await qdrant_manager.collection_exists(collection)
                    if exists:
                        count = await qdrant_manager.count_points(collection)
                        qdrant_detail["collections"][collection] = {
                            "exists": True,
                            "point_count": count
                        }
                    else:
                        qdrant_detail["collections"][collection] = {
                            "exists": False,
                            "point_count": 0
                        }
                except Exception as e:
                    qdrant_detail["collections"][collection] = {
                        "exists": False,
                        "error": str(e)
                    }
            
            services_detail["qdrant"] = qdrant_detail
            
        except Exception as e:
            services_detail["qdrant"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Neo4j详细状态
        try:
            neo4j_manager = get_neo4j_manager()
            stats = await neo4j_manager.get_graph_statistics()
            
            services_detail["neo4j"] = {
                "status": "healthy",
                "statistics": stats
            }
            
        except Exception as e:
            services_detail["neo4j"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_detail
        }
        
    except Exception as e:
        logger.error(f"获取服务详细状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")


@router.get("/health/metrics")
async def system_metrics():
    """
    获取系统性能指标
    
    Returns:
        系统性能指标
    """
    try:
        # 获取详细的系统指标
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "memory": {
                "virtual": psutil.virtual_memory()._asdict(),
                "swap": psutil.swap_memory()._asdict()
            },
            "disk": {
                "usage": psutil.disk_usage('/')._asdict(),
                "io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
            },
            "network": {
                "io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None
            },
            "processes": {
                "count": len(psutil.pids()),
                "running": len([p for p in psutil.process_iter() if p.status() == psutil.STATUS_RUNNING])
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")


@router.get("/health/ready")
async def readiness_check():
    """
    就绪检查 - 检查系统是否准备好接收请求
    
    Returns:
        就绪状态
    """
    try:
        # 检查关键服务是否就绪
        services_status = await check_services_health()
        
        # 检查是否有不健康的关键服务
        critical_services = ["qdrant", "neo4j"]
        not_ready = [
            service for service in critical_services 
            if services_status.get(service) != "healthy"
        ]
        
        if not_ready:
            return {
                "ready": False,
                "message": f"以下关键服务未就绪: {', '.join(not_ready)}",
                "services": services_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "ready": True,
            "message": "系统已就绪",
            "services": services_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"就绪检查失败: {e}")
        return {
            "ready": False,
            "message": f"就绪检查失败: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/health/live")
async def liveness_check():
    """
    存活检查 - 检查系统是否还活着
    
    Returns:
        存活状态
    """
    try:
        # 简单的存活检查
        return {
            "alive": True,
            "message": "系统正常运行",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"存活检查失败: {e}")
        return {
            "alive": False,
            "message": f"存活检查失败: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        } 