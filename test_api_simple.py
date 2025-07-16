"""
简化的AAG API服务器 - 用于集成测试
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.aag_simple import router as aag_router

app = FastAPI(
    title="AAG API - 简化版",
    description="Analysis-Augmented Generation API for Integration Testing",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(aag_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AAG API", "version": "0.1.0"}

@app.get("/")
async def root():
    return {"message": "AAG API 简化版正在运行", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)