# DPA运维手册

## 目录

1. [系统架构概览](#系统架构概览)
2. [日常运维任务](#日常运维任务)
3. [监控和告警](#监控和告警)
4. [故障处理](#故障处理)
5. [性能调优](#性能调优)
6. [安全运维](#安全运维)
7. [备份恢复](#备份恢复)
8. [容量规划](#容量规划)

## 系统架构概览

### 核心组件

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│   DPA API   │────▶│  Databases  │
│ (负载均衡)  │     │  (FastAPI)  │     │ PostgreSQL  │
└─────────────┘     └─────────────┘     │   Qdrant    │
                            │            │    Neo4j    │
                            │            │    Redis    │
                            ▼            └─────────────┘
                    ┌─────────────┐
                    │  LangGraph  │
                    │   Agents    │
                    └─────────────┘
```

### 服务端口映射

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|---------|---------|------|
| Nginx | 80/443 | 80/443 | Web入口 |
| DPA API | 8000 | - | API服务 |
| PostgreSQL | 5432 | - | 关系数据库 |
| Qdrant | 6333 | - | 向量数据库 |
| Neo4j | 7687 | - | 图数据库 |
| Redis | 6379 | - | 缓存服务 |
| Prometheus | 9090 | 9090 | 监控服务 |
| Grafana | 3000 | 3000 | 可视化 |

## 日常运维任务

### 1. 健康检查

#### 自动健康检查
```bash
# 检查所有服务状态
./scripts/deploy.sh health

# 手动检查API健康
curl http://localhost:8000/health

# 检查数据库连接
docker exec dpa-api python -c "
from src.database.postgresql import test_connection
import asyncio
asyncio.run(test_connection())
"
```

#### 服务状态检查
```bash
# Docker服务状态
docker-compose ps

# 查看资源使用
docker stats --no-stream

# Kubernetes Pod状态
kubectl get pods -n dpa -o wide
```

### 2. 日志管理

#### 日志位置
- 应用日志: `/app/logs/app.log`
- 错误日志: `/app/logs/error.log`
- Nginx日志: `/var/log/nginx/`
- 系统日志: `docker logs <container-name>`

#### 日志查看命令
```bash
# 实时查看应用日志
docker-compose logs -f dpa-api

# 查看最近100行日志
docker-compose logs --tail=100 dpa-api

# 按时间过滤日志
docker logs dpa-api --since 2024-01-01T00:00:00

# 搜索特定错误
docker logs dpa-api 2>&1 | grep ERROR
```

#### 日志轮转配置
```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "5"
```

### 3. 数据库维护

#### PostgreSQL维护
```bash
# 连接数据库
docker exec -it postgres psql -U postgres -d dpa_dev

# 查看连接数
SELECT count(*) FROM pg_stat_activity;

# 查看长时间运行的查询
SELECT pid, now() - query_start as duration, query 
FROM pg_stat_activity 
WHERE state = 'active' AND now() - query_start > interval '5 minutes';

# 终止阻塞查询
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query LIKE '%LOCK%';

# 数据库大小
SELECT pg_database_size('dpa_dev')/1024/1024 as size_mb;

# 表大小统计
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;
```

#### Qdrant维护
```bash
# 检查集合状态
curl http://rtx4080:6333/collections

# 获取集合信息
curl http://rtx4080:6333/collections/dpa_documents

# 优化集合
curl -X POST http://rtx4080:6333/collections/dpa_documents/index
```

#### Redis维护
```bash
# 连接Redis
docker exec -it redis redis-cli -a 123qwe

# 查看内存使用
INFO memory

# 查看键数量
DBSIZE

# 清理过期键
redis-cli --scan --pattern "*" | xargs -L 1 redis-cli TTL

# 查看慢查询
SLOWLOG GET 10
```

### 4. 更新部署

#### 滚动更新
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 构建新镜像
docker build -t dpa:new .

# 3. 更新服务（零停机）
docker-compose up -d --no-deps --scale dpa-api=2 dpa-api

# 4. 验证新版本
curl http://localhost:8000/ | jq .version

# 5. 完成更新
docker-compose up -d --no-deps dpa-api
```

#### 回滚操作
```bash
# 查看可用镜像
docker images | grep dpa

# 回滚到指定版本
docker-compose down
docker tag dpa:previous dpa:latest
docker-compose up -d
```

## 监控和告警

### 1. Prometheus监控指标

#### 关键指标
- **请求率**: `rate(http_requests_total[5m])`
- **错误率**: `rate(http_requests_total{status=~"5.."}[5m])`
- **响应时间**: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
- **并发请求**: `http_requests_active`

#### 自定义查询
```promql
# API响应时间P95
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)

# 每分钟错误数
sum(rate(http_requests_total{status=~"5.."}[1m])) by (endpoint)

# 数据库连接池使用率
database_pool_connections_active / database_pool_connections_total * 100

# 内存使用率
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
```

### 2. Grafana仪表板

#### 核心仪表板配置
```json
{
  "dashboard": {
    "title": "DPA系统监控",
    "panels": [
      {
        "title": "API请求率",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "响应时间",
        "targets": [{
          "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
        }]
      },
      {
        "title": "错误率",
        "targets": [{
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
        }]
      },
      {
        "title": "系统资源",
        "targets": [
          {"expr": "node_cpu_usage"},
          {"expr": "node_memory_usage"},
          {"expr": "node_disk_usage"}
        ]
      }
    ]
  }
}
```

### 3. 告警规则

#### Prometheus告警配置
```yaml
groups:
  - name: dpa_alerts
    rules:
      # API高错误率
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API错误率过高"
          description: "错误率超过5%，当前值: {{ $value }}"
      
      # 响应时间过长
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过长"
          description: "P95响应时间超过2秒"
      
      # 数据库连接池耗尽
      - alert: DatabasePoolExhausted
        expr: database_pool_connections_active >= database_pool_connections_total * 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接池即将耗尽"
          description: "连接池使用率超过90%"
      
      # 磁盘空间不足
      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "磁盘空间不足"
          description: "可用空间低于10%"
```

## 故障处理

### 1. 常见故障及处理

#### API服务无响应
```bash
# 1. 检查容器状态
docker ps -a | grep dpa-api

# 2. 查看错误日志
docker logs dpa-api --tail=50

# 3. 检查资源使用
docker stats dpa-api --no-stream

# 4. 重启服务
docker-compose restart dpa-api

# 5. 如果仍有问题，重建容器
docker-compose down
docker-compose up -d
```

#### 数据库连接失败
```bash
# 1. 测试网络连接
docker exec dpa-api ping rtx4080

# 2. 测试数据库端口
docker exec dpa-api nc -zv rtx4080 5432

# 3. 检查数据库服务
ssh rtx4080 "systemctl status postgresql"

# 4. 查看连接数
docker exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 5. 重置连接池
docker-compose restart dpa-api
```

#### 内存溢出
```bash
# 1. 查看内存使用
docker stats --no-stream

# 2. 分析内存泄漏
docker exec dpa-api python -m tracemalloc

# 3. 增加内存限制
# 修改docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# 4. 重启服务
docker-compose up -d
```

### 2. 紧急恢复流程

#### 快速恢复步骤
1. **评估影响范围**
   ```bash
   # 检查所有服务状态
   docker-compose ps
   ./scripts/deploy.sh health
   ```

2. **隔离问题服务**
   ```bash
   # 停止问题服务
   docker-compose stop dpa-api
   
   # 启动备用实例
   docker run -d --name dpa-api-backup dpa:stable
   ```

3. **恢复服务**
   ```bash
   # 使用上一个稳定版本
   docker tag dpa:stable dpa:latest
   docker-compose up -d
   ```

4. **验证恢复**
   ```bash
   # 健康检查
   curl http://localhost:8000/health
   
   # 功能测试
   ./scripts/test_basic_functionality.sh
   ```

## 性能调优

### 1. API性能优化

#### 并发配置
```python
# uvicorn配置
CMD ["uvicorn", "src.api.main:app", 
     "--workers", "4",  # 工作进程数
     "--loop", "uvloop",  # 使用uvloop提升性能
     "--limit-concurrency", "1000"]  # 最大并发连接
```

#### 连接池优化
```python
# 数据库连接池
DATABASE_POOL_SIZE = 20  # 连接池大小
DATABASE_MAX_OVERFLOW = 30  # 最大溢出连接
DATABASE_POOL_TIMEOUT = 30  # 获取连接超时
DATABASE_POOL_RECYCLE = 3600  # 连接回收时间
```

### 2. 数据库优化

#### PostgreSQL调优
```sql
-- 查看慢查询
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;

-- 创建索引
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);

-- 分析表
ANALYZE documents;
ANALYZE chunks;

-- 配置参数
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET work_mem = '64MB';
```

#### Qdrant优化
```bash
# 优化索引
curl -X POST http://rtx4080:6333/collections/dpa_documents/index

# 调整HNSW参数
{
  "hnsw_config": {
    "m": 16,
    "ef_construct": 200,
    "ef": 100
  }
}
```

### 3. 缓存优化

#### Redis缓存策略
```python
# 缓存配置
CACHE_TTL = {
    "document_metadata": 3600,  # 1小时
    "search_results": 300,      # 5分钟
    "user_session": 1800,       # 30分钟
}

# 缓存预热
def warmup_cache():
    # 预加载热门数据
    popular_docs = get_popular_documents()
    for doc in popular_docs:
        cache.set(f"doc:{doc.id}", doc, ttl=3600)
```

## 安全运维

### 1. 访问控制

#### API密钥管理
```bash
# 生成新的API密钥
openssl rand -hex 32

# 更新密钥
docker exec dpa-api python -c "
from src.utils.security import generate_api_key
print(generate_api_key())
"
```

#### 防火墙规则
```bash
# 只允许必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable

# 限制数据库访问
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -j DROP
```

### 2. 安全审计

#### 日志审计
```bash
# 审计登录尝试
grep "authentication" /app/logs/app.log | grep -E "(failed|success)"

# 审计API调用
grep "POST\|PUT\|DELETE" /var/log/nginx/access.log

# 异常行为检测
grep -E "(sql injection|xss|csrf)" /app/logs/security.log
```

#### 漏洞扫描
```bash
# 扫描Docker镜像
trivy image dpa:latest

# 扫描运行容器
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy container dpa-api

# 依赖检查
safety check -r requirements.txt
```

## 备份恢复

### 1. 自动备份

#### 备份脚本
```bash
#!/bin/bash
# /scripts/backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec postgres pg_dump -U postgres dpa_dev > $BACKUP_DIR/postgres.sql

# 备份向量数据
curl http://rtx4080:6333/collections/dpa_documents/snapshots \
  -X POST > $BACKUP_DIR/qdrant_snapshot.json

# 备份文件
tar -czf $BACKUP_DIR/uploads.tar.gz /app/data/uploads

# 清理旧备份（保留7天）
find /backups -type d -mtime +7 -exec rm -rf {} \;
```

#### Cron配置
```cron
# 每天凌晨2点备份
0 2 * * * /scripts/backup.sh >> /var/log/backup.log 2>&1

# 每周日全量备份
0 3 * * 0 /scripts/full_backup.sh >> /var/log/backup.log 2>&1
```

### 2. 恢复流程

#### 数据库恢复
```bash
# 1. 停止服务
docker-compose stop dpa-api

# 2. 恢复PostgreSQL
docker exec -i postgres psql -U postgres dpa_dev < /backups/20240701_020000/postgres.sql

# 3. 恢复Qdrant
curl http://rtx4080:6333/collections/dpa_documents/snapshots/upload \
  -X POST \
  -F "snapshot=@/backups/20240701_020000/qdrant_snapshot"

# 4. 恢复文件
tar -xzf /backups/20240701_020000/uploads.tar.gz -C /

# 5. 重启服务
docker-compose start dpa-api
```

## 容量规划

### 1. 资源监控

#### 存储增长预测
```python
# 月度存储增长率
storage_growth_rate = 0.15  # 15%每月

# 当前使用
current_usage_gb = 100

# 预测6个月后
months = 6
predicted_usage = current_usage_gb * (1 + storage_growth_rate) ** months
print(f"6个月后预计使用: {predicted_usage:.2f} GB")
```

#### 性能基准
```bash
# API基准测试
ab -n 10000 -c 100 http://localhost:8000/api/v1/health

# 数据库基准测试
pgbench -U postgres -d dpa_dev -c 10 -j 2 -t 1000

# 向量搜索基准
python scripts/benchmark_vector_search.py
```

### 2. 扩容计划

#### 垂直扩容
- CPU: 当平均使用率 > 70% 持续5分钟
- 内存: 当使用率 > 85%
- 存储: 当剩余空间 < 20%

#### 水平扩容
- API实例: 当QPS > 1000
- 数据库读副本: 当查询延迟 > 100ms
- 缓存节点: 当命中率 < 80%

### 3. 成本优化

#### 资源优化建议
1. 使用Spot实例运行非关键服务
2. 实施自动扩缩容策略
3. 定期清理未使用的数据和日志
4. 优化查询减少数据库负载
5. 使用CDN缓存静态资源

## 附录

### A. 常用命令速查

```bash
# 服务管理
docker-compose up -d          # 启动服务
docker-compose down          # 停止服务
docker-compose restart       # 重启服务
docker-compose logs -f       # 查看日志

# 健康检查
curl http://localhost:8000/health
./scripts/deploy.sh health

# 备份恢复
./scripts/backup.sh          # 执行备份
./scripts/restore.sh         # 执行恢复

# 性能监控
docker stats                 # 实时资源使用
htop                        # 系统资源监控
iotop                       # IO监控
```

### B. 故障联系人

| 角色 | 联系人 | 联系方式 |
|------|--------|----------|
| 运维负责人 | - | - |
| DBA | - | - |
| 开发负责人 | - | - |
| 安全负责人 | - | - |

### C. 相关文档

- [部署指南](DEPLOYMENT_GUIDE.md)
- [API文档](API_DOCUMENTATION.md)
- [故障处理手册](TROUBLESHOOTING.md)
- [安全规范](SECURITY_GUIDE.md)