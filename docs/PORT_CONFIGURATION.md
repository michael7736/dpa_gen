# DPA 端口配置规范

> ⚠️ **重要提醒**: 请严格遵守以下端口配置，避免误杀其他运行环境的服务

## 开发环境端口分配

### 主要服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| **后端API** | **8200** | FastAPI 主服务端口 |
| **前端Web** | **8230** | Next.js 开发服务器 |
| 后端备用1 | 8201 | 当8200被占用时自动切换 |
| 后端备用2 | 8202 | 当8201也被占用时使用 |

### 数据库服务端口（rtx4080服务器）

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 主数据库 |
| Qdrant | 6333 | 向量数据库 |
| Neo4j | 7687 | 知识图谱数据库 |
| Redis | 6379 | 缓存和会话管理 |

### 监控和调试端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Prometheus | 9090 | 性能监控 |
| Grafana | 3000 | 监控面板 |

## 启动命令

### 后端服务启动
```bash
# 标准启动（端口8200）
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload

# 或使用启动脚本（自动检测端口）
./start_api.sh
```

### 前端服务启动
```bash
cd frontend
npm run dev  # 自动使用8230端口（在package.json中配置）
```

## 端口冲突处理

### 检查端口占用
```bash
# 检查特定端口
lsof -i :8200

# 查看所有监听端口
netstat -an | grep LISTEN

# 查看进程占用的端口
ps aux | grep uvicorn
ps aux | grep "next dev"
```

### 释放端口
```bash
# 根据PID杀死进程
kill -9 <PID>

# 杀死所有uvicorn进程（谨慎使用）
pkill -f uvicorn

# 杀死特定端口的进程
kill -9 $(lsof -t -i:8200)
```

## 环境变量配置

### .env 文件配置
```env
# API配置
API_HOST=0.0.0.0
API_PORT=8200

# CORS配置（包含前端端口）
CORS_ORIGINS=["http://localhost:8230", "http://127.0.0.1:8230"]
```

### 前端环境变量
在 `frontend/.env.local` 中配置：
```env
NEXT_PUBLIC_API_URL=http://localhost:8200
```

## API访问地址

- **健康检查**: http://localhost:8200/health
- **API文档**: http://localhost:8200/docs
- **ReDoc**: http://localhost:8200/redoc
- **前端首页**: http://localhost:8230

## AAG模块测试端点

```bash
# 快速测试AAG功能
curl -X POST http://localhost:8200/api/v1/aag/skim \
  -H "X-USER-ID: u1" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "test", "document_content": "测试内容"}'
```

## 注意事项

1. **不要随意更改端口**: 所有配置文件和脚本都已经按照上述端口配置，随意更改会导致服务无法正常通信

2. **生产环境部署**: 生产环境可能使用不同的端口配置，请参考部署文档

3. **防火墙配置**: 如果在服务器上部署，需要确保相应端口在防火墙中开放

4. **端口安全**: 开发环境的端口配置仅用于本地开发，生产环境需要更严格的安全配置

## 故障排查

### 常见问题

1. **"Address already in use"错误**
   - 原因：端口被占用
   - 解决：使用上述命令查找并释放端口

2. **前端无法连接后端**
   - 检查后端是否在8200端口运行
   - 检查CORS配置是否包含8230端口
   - 检查前端的API_URL配置

3. **数据库连接失败**
   - 确认连接的是rtx4080服务器
   - 检查数据库服务是否运行
   - 验证连接字符串中的端口是否正确

## 更新历史

- 2025-01-14: 统一开发环境端口配置（后端8200，前端8230）
- 之前版本：后端使用8000/8200混合，前端使用8031