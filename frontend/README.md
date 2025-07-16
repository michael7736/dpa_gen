# DPA 智能知识引擎 - 前端

基于 Next.js 14 构建的现代化前端应用。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **UI组件**: Radix UI + 自定义组件
- **状态管理**: Zustand
- **数据请求**: React Query + Axios
- **图标**: Lucide React

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
cp .env.local.example .env.local
```

编辑 `.env.local` 文件，配置后端API地址：

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 项目结构

```
src/
├── app/                # Next.js App Router 页面
│   ├── (app)/         # 需要认证的应用页面
│   │   ├── projects/  # 项目管理
│   │   ├── documents/ # 文档管理
│   │   ├── chat/      # 智能问答
│   │   └── layout.tsx # 应用布局
│   ├── login/         # 登录页面
│   └── layout.tsx     # 根布局
├── components/        # React 组件
│   ├── ui/           # 基础UI组件
│   └── layout/       # 布局组件
├── services/         # API 服务
├── store/           # Zustand 状态管理
├── types/           # TypeScript 类型定义
└── lib/             # 工具函数和配置
```

## 主要功能

### 已实现

- ✅ 用户登录认证
- ✅ 项目管理（创建、查看、切换）
- ✅ 文档上传和管理
- ✅ 智能问答界面
- ✅ 深色模式支持
- ✅ 响应式设计

### 开发中

- 🚧 知识图谱可视化
- 🚧 文档预览
- 🚧 多语言支持
- 🚧 高级搜索

## 开发规范

### 组件开发

1. 使用函数组件和 Hooks
2. 组件文件使用 PascalCase 命名
3. 使用 TypeScript 进行类型定义
4. 遵循单一职责原则

### 样式规范

1. 使用 Tailwind CSS 进行样式开发
2. 复杂样式使用 `cn()` 工具函数组合
3. 遵循移动优先的响应式设计
4. 使用 CSS 变量管理主题色

### 状态管理

1. 全局状态使用 Zustand
2. 服务端状态使用 React Query
3. 本地状态使用 useState/useReducer
4. 避免不必要的全局状态

## 构建和部署

### 构建生产版本

```bash
npm run build
```

### 启动生产服务器

```bash
npm start
```

### Docker 部署

```bash
docker build -t dpa-frontend .
docker run -p 3000:3000 dpa-frontend
```

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| NEXT_PUBLIC_API_URL | 后端API地址 | http://localhost:8000 |

## 故障排除

### 常见问题

1. **API连接失败**
   - 检查后端服务是否启动
   - 确认 API_URL 配置正确
   - 检查跨域设置

2. **样式显示异常**
   - 清除浏览器缓存
   - 重新构建项目
   - 检查 Tailwind 配置

3. **登录失败**
   - 检查后端认证服务
   - 确认用户凭据正确
   - 查看控制台错误信息

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License