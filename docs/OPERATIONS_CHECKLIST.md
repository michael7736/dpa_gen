# DPA运维检查清单

## 日常检查清单

### 早班检查 (09:00)

- [ ] **系统健康状态**
  ```bash
  curl http://localhost:8000/health
  ./scripts/deploy.sh health
  ```

- [ ] **服务运行状态**
  ```bash
  docker-compose ps
  kubectl get pods -n dpa
  ```

- [ ] **夜间告警回顾**
  - 检查告警邮件
  - 查看Grafana告警历史
  - 处理未解决告警

- [ ] **资源使用情况**
  ```bash
  docker stats --no-stream
  df -h
  free -h
  ```

- [ ] **日志错误检查**
  ```bash
  grep ERROR /app/logs/app.log | tail -20
  docker-compose logs --since 8h | grep -i error
  ```

### 午间检查 (14:00)

- [ ] **性能指标检查**
  - API响应时间 < 200ms (P95)
  - 错误率 < 1%
  - 数据库查询时间 < 100ms

- [ ] **队列积压情况**
  ```bash
  # 检查处理队列
  redis-cli -h rtx4080 llen document_processing_queue
  ```

- [ ] **缓存命中率**
  - Redis命中率 > 80%
  - 检查缓存大小

### 晚班检查 (18:00)

- [ ] **备份验证**
  ```bash
  ls -la /backups/$(date +%Y%m%d)*
  ```

- [ ] **安全扫描结果**
  - 检查漏洞扫描报告
  - 审计异常登录

- [ ] **明日容量预测**
  - 存储空间充足
  - 数据库连接池余量

## 周常维护清单

### 周一
- [ ] **性能分析**
  - 生成上周性能报告
  - 识别性能瓶颈
  - 制定优化计划

### 周二
- [ ] **安全审计**
  - 更新依赖包
  - 扫描镜像漏洞
  - 审查访问日志

### 周三
- [ ] **数据库维护**
  ```sql
  -- 更新统计信息
  ANALYZE;
  
  -- 清理碎片
  VACUUM ANALYZE;
  
  -- 检查索引健康度
  SELECT schemaname, tablename, indexname, idx_scan
  FROM pg_stat_user_indexes
  ORDER BY idx_scan;
  ```

### 周四
- [ ] **容量规划**
  - 分析增长趋势
  - 预测资源需求
  - 规划扩容方案

### 周五
- [ ] **灾备演练**
  - 测试备份恢复
  - 验证故障切换
  - 更新应急预案

## 月度维护清单

### 第一周
- [ ] **系统更新**
  - 操作系统补丁
  - Docker版本更新
  - Kubernetes升级

- [ ] **证书检查**
  ```bash
  # 检查SSL证书过期时间
  openssl x509 -enddate -noout -in /etc/ssl/certs/dpa.crt
  ```

### 第二周
- [ ] **性能基准测试**
  ```bash
  # API压力测试
  ab -n 10000 -c 100 http://localhost:8000/api/v1/health
  
  # 数据库基准测试
  pgbench -c 10 -j 2 -t 1000 dpa_dev
  ```

### 第三周
- [ ] **架构审查**
  - 评估当前架构
  - 识别改进点
  - 规划技术债务

### 第四周
- [ ] **文档更新**
  - 更新运维手册
  - 完善故障处理流程
  - 更新架构图

## 季度维护清单

### Q1
- [ ] **年度规划**
  - 制定年度目标
  - 规划重大升级
  - 预算审核

### Q2
- [ ] **性能优化**
  - 深度性能分析
  - 实施优化方案
  - 效果评估

### Q3
- [ ] **安全加固**
  - 渗透测试
  - 安全加固
  - 合规审查

### Q4
- [ ] **年度总结**
  - 可用性统计
  - 事故分析
  - 改进计划

## 紧急事件检查清单

### 服务中断
1. [ ] 确认影响范围
2. [ ] 启动应急预案
3. [ ] 通知相关人员
4. [ ] 记录时间线
5. [ ] 快速止损
6. [ ] 根因分析
7. [ ] 制定修复方案
8. [ ] 验证恢复
9. [ ] 编写事故报告

### 数据泄露
1. [ ] 立即隔离系统
2. [ ] 保存现场证据
3. [ ] 通知安全团队
4. [ ] 评估影响范围
5. [ ] 通知受影响用户
6. [ ] 修复漏洞
7. [ ] 加强监控
8. [ ] 提交合规报告

### 性能危机
1. [ ] 识别瓶颈点
2. [ ] 临时扩容
3. [ ] 限流降级
4. [ ] 优化查询
5. [ ] 清理缓存
6. [ ] 监控恢复

## 部署检查清单

### 部署前
- [ ] 代码审查通过
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 安全扫描通过
- [ ] 文档更新完成
- [ ] 回滚方案准备

### 部署中
- [ ] 备份当前版本
- [ ] 更新配置文件
- [ ] 执行数据库迁移
- [ ] 部署新版本
- [ ] 健康检查通过
- [ ] 冒烟测试通过

### 部署后
- [ ] 监控关键指标
- [ ] 验证功能正常
- [ ] 性能对比分析
- [ ] 用户反馈收集
- [ ] 问题快速响应
- [ ] 部署总结报告

## 值班交接清单

### 交接内容
- [ ] **当前系统状态**
  - 各服务运行状态
  - 未解决的告警
  - 进行中的任务

- [ ] **重要事项**
  - 计划内维护
  - 已知问题
  - 特殊关注点

- [ ] **历史记录**
  - 值班期间事件
  - 处理过程
  - 遗留问题

### 交接确认
- [ ] 接班人员了解当前状态
- [ ] 相关文档已更新
- [ ] 权限已正确传递
- [ ] 紧急联系方式确认

## 工具和资源

### 常用命令
```bash
# 快速健康检查
alias health='curl -s http://localhost:8000/health | jq'

# 查看错误日志
alias errors='docker-compose logs --tail=50 | grep ERROR'

# 资源使用情况
alias resources='docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
```

### 监控面板
- [系统概览](http://grafana:3000/d/system)
- [业务指标](http://grafana:3000/d/business)
- [告警中心](http://grafana:3000/d/alerts)

### 文档链接
- [运维手册](OPERATIONS_MANUAL.md)
- [监控指南](MONITORING_GUIDE.md)
- [故障处理](TROUBLESHOOTING.md)
- [部署指南](DEPLOYMENT_GUIDE.md)