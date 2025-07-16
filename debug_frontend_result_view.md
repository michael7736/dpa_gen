# 前端结果查看功能调试指南

## 问题诊断

用户反馈："摘要生成后点击查看结果没有反应"

## 可能原因分析

### 1. 组件属性不匹配 ✅ 已修复
- **原因**: ResultViewModal组件期望`actionType`属性，但AAG页面传递的是`viewType`
- **解决**: 已将`viewType`改为`actionType`，并添加了`documentName`属性

### 2. API端点缺失 ✅ 已修复
- **原因**: 后端缺少`/api/v1/documents/{document_id}/summary`端点
- **解决**: 已在documents.py中添加了完整的API端点

### 3. 数据库查询问题 ⚠️ 需要验证
- **原因**: 摘要数据可能没有正确保存到数据库
- **检查**: 需要验证processing_stage表中是否有正确的摘要数据

## 调试步骤

### 前端调试

1. **浏览器控制台检查**
   ```javascript
   // 打开浏览器控制台 (F12)
   // 点击"查看结果"按钮后查看是否有错误
   ```

2. **网络请求检查**
   ```javascript
   // 在Network标签中检查API请求
   // 查看是否有404或500错误
   ```

3. **组件状态检查**
   ```javascript
   // 在React DevTools中检查组件状态
   // 验证resultModalOpen是否变为true
   ```

### 后端调试

1. **API端点测试**
   ```bash
   # 测试健康检查
   curl -H "X-USER-ID: u1" http://localhost:8200/api/v1/health
   
   # 测试文档列表
   curl -H "X-USER-ID: u1" http://localhost:8200/api/v1/documents
   
   # 测试文档摘要 (替换{document_id})
   curl -H "X-USER-ID: u1" http://localhost:8200/api/v1/documents/{document_id}/summary
   ```

2. **数据库查询验证**
   ```sql
   -- 检查文档表
   SELECT id, filename, processing_status FROM documents;
   
   -- 检查处理管道
   SELECT id, document_id, overall_progress, completed FROM processing_pipelines;
   
   -- 检查处理阶段
   SELECT id, pipeline_id, stage_type, status, result_data FROM processing_stages 
   WHERE stage_type = 'summary' AND status = 'completed';
   ```

## 常见问题解决

### 问题1: 模态框不弹出
**解决方法:**
```typescript
// 在handleViewResult函数中添加调试日志
const handleViewResult = (action: 'summary' | 'index' | 'analysis', documentId: string) => {
  console.log('handleViewResult called:', action, documentId);
  setResultModalType(action);
  setResultModalDocumentId(documentId);
  setResultModalOpen(true);
  console.log('Modal should open:', resultModalOpen);
}
```

### 问题2: API返回404错误
**解决方法:**
```typescript
// 检查documentId格式是否正确
// 确保后端API端点已正确注册
// 验证数据库中是否存在对应的摘要数据
```

### 问题3: 权限认证问题
**解决方法:**
```typescript
// 确保请求头包含正确的用户ID
headers: {
  'X-USER-ID': 'u1',
  'Content-Type': 'application/json'
}
```

## 测试步骤

1. **启动后端服务**
   ```bash
   cd /Users/mdwong001/Desktop/code/rag/DPA
   uvicorn src.api.main:app --reload --port 8200
   ```

2. **启动前端服务**
   ```bash
   cd frontend
   npm run dev
   ```

3. **执行测试流程**
   - 访问 http://localhost:8230/aag
   - 上传文档并启用摘要生成
   - 等待摘要生成完成
   - 点击"查看结果"按钮
   - 检查模态框是否正常弹出

## 修复状态

- ✅ 组件属性修复
- ✅ API端点添加
- ✅ 前端集成完成
- ⚠️ 需要验证数据库查询
- ⚠️ 需要测试完整流程

## 下一步行动

1. 启动后端和前端服务
2. 测试文档上传和摘要生成
3. 验证"查看结果"功能
4. 如有问题，检查浏览器控制台和网络请求
5. 必要时检查数据库数据完整性