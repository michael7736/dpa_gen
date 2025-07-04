# DPA部署指南

## 概述

本指南详细说明了DPA智能知识引擎的部署流程，包括Docker部署、Kubernetes部署和生产环境优化。

## 快速开始

### 1. 环境准备

确保系统已安装：
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 2. 克隆项目

```bash
git clone https://github.com/your-org/dpa.git
cd dpa
```

### 3. 配置环境变量

```bash
cp .env.template .env
# 编辑.env文件，配置必要的环境变量
```

### 4. 快速部署

```bash
# 开发环境
./scripts/deploy.sh deploy dev

# 生产环境
./scripts/deploy.sh deploy prod
```

## Docker部署

### 构建镜像

使用多阶段构建优化镜像大小：

```bash
# 构建镜像
docker build -t dpa:latest .

# 使用BuildKit加速构建
DOCKER_BUILDKIT=1 docker build -t dpa:latest .
```

### 本地开发环境

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f dpa-api

# 停止服务
docker-compose down
```

### 生产环境部署

```bash
# 使用生产配置
docker-compose -f docker-compose.prod.yml up -d

# 扩展服务实例
docker-compose -f docker-compose.prod.yml up -d --scale dpa-api=3
```

## Kubernetes部署

### 1. 创建命名空间

```bash
kubectl create namespace dpa
```

### 2. 创建配置和密钥

```bash
# 创建ConfigMap
kubectl create configmap dpa-config \
  --from-literal=qdrant-url=http://rtx4080:6333 \
  --from-literal=neo4j-url=bolt://rtx4080:7687 \
  -n dpa

# 创建Secret
kubectl create secret generic dpa-secrets \
  --from-literal=database-url=postgresql://user:pass@host:5432/db \
  --from-literal=redis-url=redis://:pass@host:6379/0 \
  --from-literal=openrouter-api-key=your-api-key \
  -n dpa
```

### 3. 部署应用

```bash
# 部署应用
kubectl apply -f deploy/k8s/deployment.yaml

# 检查部署状态
kubectl get deployments -n dpa
kubectl get pods -n dpa
```

### 4. 配置Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dpa-ingress
  namespace: dpa
spec:
  rules:
  - host: dpa.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dpa-api-service
            port:
              number: 8000
```

## 性能优化

### 1. Docker镜像优化

- 使用多阶段构建减少镜像大小
- 使用Alpine Linux作为基础镜像
- 只安装必要的运行时依赖
- 使用.dockerignore排除不必要的文件

### 2. 应用性能优化

```yaml
# docker-compose.prod.yml
environment:
  # 工作进程数
  WORKERS: 4
  # 并发请求数
  MAX_CONCURRENT_REQUESTS: 100
  # 连接池大小
  DATABASE_POOL_SIZE: 20
  # 缓存配置
  REDIS_CACHE_TTL: 3600
```

### 3. Nginx优化

- 启用Gzip压缩
- 配置缓存策略
- 使用上游负载均衡
- 限流保护

### 4. 资源限制

```yaml
# Kubernetes资源配置
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## 监控和日志

### 1. Prometheus监控

```bash
# 访问Prometheus
http://localhost:9090

# 查询示例
rate(http_requests_total[5m])
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

### 2. Grafana可视化

```bash
# 访问Grafana
http://localhost:3000
# 默认用户名/密码: admin/admin

# 导入仪表板
1. 添加Prometheus数据源
2. 导入deploy/grafana/dashboards/dpa-dashboard.json
```

### 3. 日志收集

```bash
# 查看容器日志
docker logs -f dpa-api

# 使用Fluentd收集日志（生产环境）
docker-compose -f docker-compose.prod.yml logs fluentd
```

## 安全配置

### 1. HTTPS配置

```nginx
server {
    listen 443 ssl http2;
    server_name dpa.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### 2. 安全最佳实践

- 使用非root用户运行容器
- 限制容器capabilities
- 使用只读文件系统（where possible）
- 定期更新基础镜像
- 扫描镜像漏洞

### 3. 密钥管理

- 使用Kubernetes Secrets管理敏感信息
- 启用Secret加密
- 定期轮换密钥
- 使用外部密钥管理服务（如Vault）

## 故障排查

### 常见问题

1. **容器无法启动**
   ```bash
   # 检查日志
   docker logs dpa-api
   
   # 检查环境变量
   docker exec dpa-api env
   ```

2. **数据库连接失败**
   ```bash
   # 测试连接
   docker exec dpa-api python -c "from src.database.postgresql import test_connection; import asyncio; asyncio.run(test_connection())"
   ```

3. **性能问题**
   ```bash
   # 查看资源使用
   docker stats dpa-api
   
   # 检查慢查询
   docker exec -it postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

### 健康检查

```bash
# 手动健康检查
curl http://localhost:8000/health

# 查看容器健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 备份和恢复

### 备份策略

```bash
# 执行备份
./scripts/deploy.sh backup

# 自动备份（使用cron）
0 2 * * * /path/to/dpa/scripts/deploy.sh backup
```

### 恢复流程

```bash
# 1. 停止服务
docker-compose down

# 2. 恢复数据
cp -r backups/20240101_020000/* data/

# 3. 重启服务
docker-compose up -d
```

## 升级流程

### 1. 准备新版本

```bash
# 拉取最新代码
git pull origin main

# 构建新镜像
docker build -t dpa:new-version .
```

### 2. 滚动更新

```bash
# Kubernetes滚动更新
kubectl set image deployment/dpa-api dpa-api=dpa:new-version -n dpa

# Docker Compose更新
docker-compose up -d --no-deps --build dpa-api
```

### 3. 验证更新

```bash
# 检查版本
curl http://localhost:8000/

# 运行健康检查
./scripts/deploy.sh health
```

## 生产环境清单

- [ ] 配置HTTPS证书
- [ ] 启用防火墙规则
- [ ] 配置备份策略
- [ ] 设置监控告警
- [ ] 优化数据库索引
- [ ] 配置日志轮转
- [ ] 设置资源限制
- [ ] 启用安全扫描
- [ ] 配置CDN（如需要）
- [ ] 准备灾难恢复计划