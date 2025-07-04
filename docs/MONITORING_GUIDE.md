# DPA监控指南

## 概述

本指南详细介绍DPA系统的监控架构、指标收集、可视化配置和告警策略。

## 监控架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   DPA API   │────▶│ Prometheus  │────▶│   Grafana   │
│  (Metrics)  │     │ (收集存储)  │     │  (可视化)   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │ AlertManager│
                    │   (告警)    │
                    └─────────────┘
```

## 指标收集

### 1. 应用指标

#### FastAPI Metrics
```python
# src/api/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# 请求计数器
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 请求延迟直方图
request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# 活跃请求数
active_requests = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

# 中间件实现
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    active_requests.inc()
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as e:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        active_requests.dec()
        
        # 记录指标
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status
        ).inc()
        
        request_latency.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
    
    return response
```

#### 业务指标
```python
# 文档处理指标
document_processed = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['status', 'type']
)

processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration',
    ['type']
)

# 向量搜索指标
vector_search_count = Counter(
    'vector_searches_total',
    'Total vector searches performed'
)

search_latency = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration'
)

# 缓存指标
cache_hits = Counter('cache_hits_total', 'Cache hits')
cache_misses = Counter('cache_misses_total', 'Cache misses')
```

### 2. 系统指标

#### Node Exporter配置
```yaml
# docker-compose.yml
node-exporter:
  image: prom/node-exporter:latest
  container_name: node-exporter
  ports:
    - "9100:9100"
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/rootfs:ro
  command:
    - '--path.procfs=/host/proc'
    - '--path.sysfs=/host/sys'
    - '--path.rootfs=/rootfs'
```

#### 收集的系统指标
- CPU使用率: `node_cpu_seconds_total`
- 内存使用: `node_memory_MemAvailable_bytes`
- 磁盘IO: `node_disk_io_time_seconds_total`
- 网络流量: `node_network_receive_bytes_total`
- 文件系统: `node_filesystem_avail_bytes`

### 3. 数据库指标

#### PostgreSQL Exporter
```yaml
postgres-exporter:
  image: wrouesnel/postgres_exporter:latest
  environment:
    DATA_SOURCE_NAME: "postgresql://user:pass@postgres:5432/dpa?sslmode=disable"
  ports:
    - "9187:9187"
```

#### 关键数据库指标
```sql
-- 自定义查询配置
pg_database:
  query: "SELECT pg_database.datname, pg_database_size(pg_database.datname) as size FROM pg_database"
  metrics:
    - datname:
        usage: "LABEL"
    - size:
        usage: "GAUGE"

pg_connections:
  query: "SELECT count(*) as total, state FROM pg_stat_activity GROUP BY state"
  metrics:
    - total:
        usage: "GAUGE"
    - state:
        usage: "LABEL"
```

## Grafana配置

### 1. 数据源配置

```yaml
# deploy/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

### 2. 仪表板配置

#### 系统概览仪表板
```json
{
  "dashboard": {
    "title": "DPA系统概览",
    "panels": [
      {
        "title": "请求率",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [{
          "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
          "legendFormat": "{{endpoint}}"
        }]
      },
      {
        "title": "错误率",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [{
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (endpoint)",
          "legendFormat": "{{endpoint}}"
        }]
      },
      {
        "title": "响应时间P95",
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
        "targets": [{
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
          "legendFormat": "{{endpoint}}"
        }]
      },
      {
        "title": "系统资源",
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU使用率"
          },
          {
            "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "legendFormat": "内存使用率"
          }
        ]
      }
    ]
  }
}
```

#### 业务指标仪表板
```json
{
  "dashboard": {
    "title": "DPA业务指标",
    "panels": [
      {
        "title": "文档处理速率",
        "targets": [{
          "expr": "sum(rate(documents_processed_total[5m])) by (type)"
        }]
      },
      {
        "title": "处理成功率",
        "targets": [{
          "expr": "sum(rate(documents_processed_total{status=\"success\"}[5m])) / sum(rate(documents_processed_total[5m])) * 100"
        }]
      },
      {
        "title": "搜索QPS",
        "targets": [{
          "expr": "sum(rate(vector_searches_total[1m]))"
        }]
      },
      {
        "title": "缓存命中率",
        "targets": [{
          "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100"
        }]
      }
    ]
  }
}
```

### 3. 告警仪表板

```json
{
  "dashboard": {
    "title": "告警概览",
    "panels": [
      {
        "title": "活跃告警",
        "type": "table",
        "targets": [{
          "expr": "ALERTS{alertstate=\"firing\"}"
        }]
      },
      {
        "title": "告警历史",
        "type": "graph",
        "targets": [{
          "expr": "ALERTS"
        }]
      }
    ]
  }
}
```

## 告警配置

### 1. Prometheus告警规则

```yaml
# deploy/prometheus/alerts/dpa-alerts.yml
groups:
  - name: dpa_application
    interval: 30s
    rules:
      # API可用性
      - alert: APIDown
        expr: up{job="dpa-api"} == 0
        for: 1m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "DPA API服务宕机"
          description: "{{ $labels.instance }} 已经宕机超过1分钟"
          
      # 高错误率
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint)
          /
          sum(rate(http_requests_total[5m])) by (endpoint)
          > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高错误率检测"
          description: "端点 {{ $labels.endpoint }} 错误率超过5%"
          
      # 响应时间
      - alert: SlowResponse
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应缓慢"
          description: "端点 {{ $labels.endpoint }} P95响应时间超过2秒"

  - name: dpa_resources
    interval: 30s
    rules:
      # CPU使用率
      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "{{ $labels.instance }} CPU使用率超过80%"
          
      # 内存使用
      - alert: HighMemoryUsage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "{{ $labels.instance }} 内存使用率超过85%"
          
      # 磁盘空间
      - alert: DiskSpaceLow
        expr: |
          node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足"
          description: "{{ $labels.instance }} 根分区可用空间低于10%"

  - name: dpa_database
    interval: 30s
    rules:
      # 数据库连接
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          pg_stat_activity_count / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "数据库连接池即将耗尽"
          description: "连接使用率超过80%"
          
      # 慢查询
      - alert: DatabaseSlowQueries
        expr: |
          rate(pg_stat_statements_mean_time_seconds[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "检测到慢查询"
          description: "平均查询时间超过1秒"
```

### 2. AlertManager配置

```yaml
# deploy/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_from: 'dpa-alerts@example.com'
  smtp_smarthost: 'smtp.example.com:587'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true
    - match:
        severity: warning
      receiver: 'warning'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops-team@example.com'
        
  - name: 'critical'
    email_configs:
      - to: 'ops-oncall@example.com'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'
        
  - name: 'warning'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#dpa-alerts'
        title: 'DPA Warning Alert'
```

## 日志聚合

### 1. Loki配置

```yaml
# docker-compose.yml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./deploy/loki/loki-config.yml:/etc/loki/local-config.yaml
    - loki-data:/loki

promtail:
  image: grafana/promtail:latest
  volumes:
    - ./logs:/var/log/dpa:ro
    - ./deploy/promtail/promtail-config.yml:/etc/promtail/config.yml
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

### 2. Promtail配置

```yaml
# deploy/promtail/promtail-config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: dpa
    static_configs:
      - targets:
          - localhost
        labels:
          job: dpa
          __path__: /var/log/dpa/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            timestamp: timestamp
            message: message
      - labels:
          level:
      - timestamp:
          source: timestamp
          format: RFC3339
```

### 3. 日志查询示例

```logql
# 查看所有错误日志
{job="dpa"} |= "ERROR"

# 特定端点的错误
{job="dpa"} |~ "endpoint=\"/api/v1/documents\"" |= "ERROR"

# 响应时间大于1秒的请求
{job="dpa"} | json | duration > 1

# 统计每分钟错误数
sum(rate({job="dpa", level="ERROR"}[1m]))
```

## 自定义监控

### 1. 业务监控脚本

```python
# scripts/monitor_business_metrics.py
import asyncio
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from src.database.postgresql import get_session
from sqlalchemy import select, func

registry = CollectorRegistry()

# 定义业务指标
total_documents = Gauge('dpa_total_documents', 'Total documents in system', registry=registry)
total_users = Gauge('dpa_total_users', 'Total registered users', registry=registry)
avg_processing_time = Gauge('dpa_avg_processing_time', 'Average document processing time', registry=registry)

async def collect_metrics():
    async with get_session() as session:
        # 收集文档总数
        doc_count = await session.scalar(select(func.count()).select_from(Document))
        total_documents.set(doc_count)
        
        # 收集用户总数
        user_count = await session.scalar(select(func.count()).select_from(User))
        total_users.set(user_count)
        
        # 收集平均处理时间
        avg_time = await session.scalar(
            select(func.avg(Document.processing_time)).where(
                Document.status == 'completed'
            )
        )
        if avg_time:
            avg_processing_time.set(avg_time)
    
    # 推送到Prometheus
    push_to_gateway('localhost:9091', job='dpa_business', registry=registry)

if __name__ == "__main__":
    asyncio.run(collect_metrics())
```

### 2. 健康检查监控

```python
# scripts/health_monitor.py
import httpx
import asyncio
from prometheus_client import Counter, Gauge

# 健康检查指标
health_check_total = Counter('health_checks_total', 'Total health checks performed')
health_check_failures = Counter('health_check_failures_total', 'Failed health checks')
service_health_status = Gauge('service_health_status', 'Service health status', ['service'])

async def check_service_health():
    services = {
        'api': 'http://localhost:8000/health',
        'prometheus': 'http://localhost:9090/-/healthy',
        'grafana': 'http://localhost:3000/api/health'
    }
    
    async with httpx.AsyncClient() as client:
        for service, url in services.items():
            try:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    service_health_status.labels(service=service).set(1)
                else:
                    service_health_status.labels(service=service).set(0)
                    health_check_failures.inc()
            except Exception as e:
                service_health_status.labels(service=service).set(0)
                health_check_failures.inc()
                print(f"Health check failed for {service}: {e}")
            
            health_check_total.inc()

async def main():
    while True:
        await check_service_health()
        await asyncio.sleep(30)  # 每30秒检查一次

if __name__ == "__main__":
    asyncio.run(main())
```

## 性能分析

### 1. APM集成

```python
# 集成OpenTelemetry
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 配置追踪
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# 使用追踪
@app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str):
    with tracer.start_as_current_span("get_document") as span:
        span.set_attribute("document.id", doc_id)
        # 业务逻辑
        return document
```

### 2. 性能剖析

```python
# 使用py-spy进行性能剖析
# 安装: pip install py-spy

# 实时查看性能
# py-spy top --pid $(pgrep -f "uvicorn")

# 生成火焰图
# py-spy record -o profile.svg --pid $(pgrep -f "uvicorn") --duration 60
```

## 监控最佳实践

### 1. 指标命名规范

- 使用小写字母和下划线
- 包含单位后缀（_seconds, _bytes, _total）
- 使用有意义的标签
- 避免高基数标签

### 2. 仪表板设计原则

- 从概览到详细的层次结构
- 使用一致的时间范围
- 合理使用颜色和阈值
- 包含相关的上下文信息

### 3. 告警策略

- 避免告警疲劳
- 设置合理的阈值和时间窗口
- 包含清晰的处理步骤
- 定期审查和优化告警规则

### 4. 性能优化建议

- 合理设置数据保留期
- 使用recording rules预计算
- 优化查询避免高消耗
- 定期清理无用指标