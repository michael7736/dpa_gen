# Chatbot文档处理实现示例

## 1. 核心对话处理示例

### 1.1 主对话处理器
```python
# src/services/chatbot_service.py

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

class ChatbotService:
    """
    Chatbot核心服务
    """
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.workflow_engine = WorkflowEngine()
        self.intent_recognizer = IntentRecognizer()
        
    async def process_message(
        self,
        user_id: str,
        message: str,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息并返回响应
        """
        # 1. 获取或创建会话
        session = await self.conversation_manager.get_or_create_session(
            user_id, session_id
        )
        
        # 2. 如果有新文档，触发工作流
        if document_id and not session.document_id:
            session.document_id = document_id
            return await self._handle_new_document(session, document_id)
        
        # 3. 识别意图
        intent = await self.intent_recognizer.recognize(
            message, 
            session.get_context()
        )
        
        # 4. 根据当前状态和意图处理
        response = await self._handle_intent(session, intent, message)
        
        # 5. 更新会话历史
        session.add_message("user", message)
        session.add_message("assistant", response["content"])
        
        # 6. 保存会话状态
        await self.conversation_manager.save_session(session)
        
        return response
    
    async def _handle_new_document(
        self, 
        session: Session, 
        document_id: str
    ) -> Dict[str, Any]:
        """处理新上传的文档"""
        # 获取文档信息
        doc_info = await self.get_document_info(document_id)
        
        # 创建工作流
        workflow = await self.workflow_engine.create_workflow(
            document_id=document_id,
            user_id=session.user_id,
            document_type=doc_info["type"]
        )
        
        session.workflow_id = workflow.id
        session.state = ConversationState.PROCESSING_SELECTION
        
        # 生成智能建议
        suggestions = self._generate_processing_suggestions(doc_info)
        
        return {
            "content": f"📄 文档 \"{doc_info['filename']}\" 已成功上传！\n\n"
                      f"文件大小：{doc_info['size_mb']:.1f}MB，"
                      f"共{doc_info['page_count']}页\n\n"
                      f"我注意到这是一份{doc_info['document_type']}，"
                      f"建议进行以下处理：\n\n"
                      f"{suggestions}\n\n"
                      f"您想从哪个开始？或者有其他需求？",
            "actions": [
                {"label": "🔍 快速摘要", "action": "summary"},
                {"label": "📑 创建索引", "action": "index"},
                {"label": "🧠 深度分析", "action": "analyze"},
                {"label": "💡 我有其他需求", "action": "custom"}
            ],
            "metadata": {
                "document_id": document_id,
                "workflow_id": workflow.id,
                "state": "processing_selection"
            }
        }
```

### 1.2 意图处理器
```python
async def _handle_intent(
    self,
    session: Session,
    intent: Intent,
    original_message: str
) -> Dict[str, Any]:
    """根据意图处理消息"""
    
    handlers = {
        IntentType.SUMMARY: self._handle_summary_intent,
        IntentType.INDEX: self._handle_index_intent,
        IntentType.ANALYZE: self._handle_analyze_intent,
        IntentType.STATUS: self._handle_status_intent,
        IntentType.INTERRUPT: self._handle_interrupt_intent,
        IntentType.CONTINUE: self._handle_continue_intent,
        IntentType.CUSTOM: self._handle_custom_intent
    }
    
    handler = handlers.get(intent.type, self._handle_unknown_intent)
    return await handler(session, intent, original_message)

async def _handle_summary_intent(
    self,
    session: Session,
    intent: Intent,
    message: str
) -> Dict[str, Any]:
    """处理摘要请求"""
    
    # 检查是否有特定要求
    focus_areas = self._extract_focus_areas(message)
    
    # 更新工作流参数
    if focus_areas:
        await self.workflow_engine.update_parameters(
            session.workflow_id,
            {"summary_focus": focus_areas}
        )
    
    # 启动摘要任务
    task = await self.workflow_engine.start_stage(
        session.workflow_id,
        "summary"
    )
    
    session.state = ConversationState.SUMMARY_IN_PROGRESS
    
    # 启动进度监控
    asyncio.create_task(
        self._monitor_progress(session, task.id)
    )
    
    response_text = "🚀 开始生成摘要...\n\n"
    if focus_areas:
        response_text += f"我会特别关注：{', '.join(focus_areas)}\n\n"
    
    return {
        "content": response_text,
        "streaming": True,  # 表示会有实时更新
        "metadata": {
            "task_id": task.id,
            "stage": "summary",
            "estimated_time": 30
        }
    }
```

### 1.3 进度监控器
```python
async def _monitor_progress(self, session: Session, task_id: str):
    """监控任务进度并推送更新"""
    
    last_progress = 0
    
    while True:
        # 获取任务状态
        task_status = await self.workflow_engine.get_task_status(task_id)
        
        # 推送进度更新
        if task_status.progress > last_progress:
            await self._push_progress_update(
                session.user_id,
                {
                    "task_id": task_id,
                    "stage": task_status.stage,
                    "progress": task_status.progress,
                    "message": task_status.current_step,
                    "preview": task_status.preview_data
                }
            )
            last_progress = task_status.progress
        
        # 检查是否完成
        if task_status.status in ["completed", "failed", "interrupted"]:
            break
            
        # 检查是否被中断
        if session.interruption_requested:
            await self.workflow_engine.interrupt_task(task_id)
            break
            
        await asyncio.sleep(1)  # 每秒检查一次
    
    # 处理完成后的逻辑
    if task_status.status == "completed":
        await self._handle_stage_complete(session, task_status)
```

## 2. 工作流引擎实现

### 2.1 工作流定义
```python
# src/workflows/document_workflow.py

class DocumentProcessingWorkflow:
    """
    文档处理工作流
    """
    def __init__(self, document_id: str, user_id: str):
        self.document_id = document_id
        self.user_id = user_id
        self.stages = self._define_stages()
        self.current_stage_index = 0
        self.state = WorkflowState.INITIALIZED
        self.context = {}
        
    def _define_stages(self):
        return [
            WorkflowStage(
                id="init",
                name="初始化",
                handler=self._init_handler,
                skippable=False
            ),
            WorkflowStage(
                id="summary",
                name="生成摘要",
                handler=self._summary_handler,
                interruptible=True,
                conditions=["user_requested", "auto_suggested"]
            ),
            WorkflowStage(
                id="index",
                name="创建索引",
                handler=self._index_handler,
                interruptible=True,
                conditions=["user_requested", "summary_completed"]
            ),
            WorkflowStage(
                id="analysis",
                name="深度分析",
                handler=self._analysis_handler,
                interruptible=True,
                conditions=["user_requested", "index_completed"]
            )
        ]
    
    async def _summary_handler(self, params: Dict[str, Any]):
        """摘要生成处理器"""
        # 1. 准备参数
        focus_areas = params.get("summary_focus", [])
        
        # 2. 创建摘要任务
        summary_service = SummaryService()
        
        # 3. 生成摘要（带进度回调）
        async def progress_callback(progress: int, message: str, preview: Any = None):
            await self._update_progress("summary", progress, message, preview)
        
        result = await summary_service.generate_summary(
            document_id=self.document_id,
            focus_areas=focus_areas,
            progress_callback=progress_callback
        )
        
        # 4. 保存结果到上下文
        self.context["summary_result"] = result
        
        # 5. 生成下一步建议
        next_suggestions = self._generate_next_suggestions("summary", result)
        
        return {
            "success": True,
            "result": result,
            "next_suggestions": next_suggestions
        }
```

### 2.2 中断和恢复机制
```python
class InterruptibleStage:
    """
    可中断的处理阶段
    """
    def __init__(self, stage_id: str):
        self.stage_id = stage_id
        self.checkpoint_data = {}
        self.is_interrupted = False
        
    async def execute_with_interruption(self, handler, params):
        """执行可中断的任务"""
        try:
            # 设置中断检查点
            self.set_checkpoint_handler()
            
            # 执行任务
            result = await handler(params)
            
            return result
            
        except InterruptedException:
            # 保存中断点数据
            await self.save_checkpoint()
            return {
                "success": False,
                "interrupted": True,
                "checkpoint": self.checkpoint_data
            }
    
    async def resume_from_checkpoint(self, user_input: Optional[str] = None):
        """从中断点恢复"""
        # 加载检查点数据
        checkpoint = await self.load_checkpoint()
        
        # 如果用户提供了新输入，更新参数
        if user_input:
            checkpoint["params"].update(
                self._parse_user_input(user_input)
            )
        
        # 从中断点继续执行
        return await self.continue_execution(checkpoint)
```

## 3. 实时通信实现

### 3.1 WebSocket处理器
```python
# src/api/websocket_handler.py

class ChatbotWebSocketHandler:
    """
    Chatbot WebSocket处理器
    """
    def __init__(self, websocket: WebSocket, user_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.chatbot_service = ChatbotService()
        
    async def handle_connection(self):
        """处理WebSocket连接"""
        try:
            # 发送欢迎消息
            await self.send_message({
                "type": "connected",
                "message": "连接成功，我是您的文档处理助手"
            })
            
            # 处理消息循环
            while True:
                data = await self.websocket.receive_json()
                await self.handle_message(data)
                
        except WebSocketDisconnect:
            logger.info(f"用户 {self.user_id} 断开连接")
            
    async def handle_message(self, data: dict):
        """处理收到的消息"""
        message_type = data.get("type")
        
        if message_type == "chat":
            # 处理聊天消息
            response = await self.chatbot_service.process_message(
                user_id=self.user_id,
                message=data["content"],
                document_id=data.get("document_id"),
                session_id=data.get("session_id")
            )
            await self.send_message(response)
            
        elif message_type == "action":
            # 处理动作按钮点击
            await self.handle_action(data["action"], data.get("params"))
            
        elif message_type == "interrupt":
            # 处理中断请求
            await self.handle_interrupt(data.get("session_id"))
```

### 3.2 进度推送服务
```python
class ProgressPusher:
    """
    进度推送服务
    """
    def __init__(self, websocket_manager):
        self.ws_manager = websocket_manager
        
    async def push_progress(
        self,
        user_id: str,
        stage: str,
        progress: int,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """推送进度更新"""
        await self.ws_manager.send_to_user(user_id, {
            "type": "progress",
            "data": {
                "stage": stage,
                "progress": progress,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    async def stream_result(
        self,
        user_id: str,
        stage: str,
        content_generator
    ):
        """流式推送结果"""
        buffer = ""
        async for chunk in content_generator:
            buffer += chunk
            
            # 每积累一定内容就推送
            if len(buffer) >= 100 or chunk.endswith("\n"):
                await self.ws_manager.send_to_user(user_id, {
                    "type": "stream",
                    "data": {
                        "stage": stage,
                        "content": buffer,
                        "complete": False
                    }
                })
                buffer = ""
        
        # 推送剩余内容
        if buffer:
            await self.ws_manager.send_to_user(user_id, {
                "type": "stream",
                "data": {
                    "stage": stage,
                    "content": buffer,
                    "complete": True
                }
            })
```

## 4. 前端实现示例

### 4.1 增强的Chatbot组件
```typescript
// frontend/src/components/aag/EnhancedAIChat.tsx

import { useState, useEffect, useCallback } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'

interface EnhancedAIChatProps {
  documentId?: string
  onWorkflowUpdate?: (workflow: WorkflowState) => void
}

export function EnhancedAIChat({ documentId, onWorkflowUpdate }: EnhancedAIChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowState>()
  const [isProcessing, setIsProcessing] = useState(false)
  
  const { sendMessage, lastMessage, connectionStatus } = useWebSocket()
  
  // 处理WebSocket消息
  useEffect(() => {
    if (!lastMessage) return
    
    const data = JSON.parse(lastMessage)
    
    switch (data.type) {
      case 'chat':
        handleChatResponse(data)
        break
      case 'progress':
        handleProgressUpdate(data.data)
        break
      case 'stream':
        handleStreamUpdate(data.data)
        break
      case 'workflow_update':
        handleWorkflowUpdate(data.data)
        break
    }
  }, [lastMessage])
  
  // 处理聊天响应
  const handleChatResponse = (response: any) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'assistant',
      content: response.content,
      timestamp: new Date(),
      actions: response.actions?.map(action => ({
        ...action,
        onClick: () => handleAction(action.action)
      }))
    }
    
    setMessages(prev => [...prev, newMessage])
    
    if (response.metadata?.workflow_id) {
      setCurrentWorkflow({
        id: response.metadata.workflow_id,
        state: response.metadata.state
      })
    }
  }
  
  // 处理进度更新
  const handleProgressUpdate = (progress: ProgressData) => {
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1]
      if (lastMessage?.type === 'assistant') {
        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            progress: {
              stage: progress.stage,
              percent: progress.progress,
              message: progress.message,
              preview: progress.details?.preview
            }
          }
        ]
      }
      return prev
    })
  }
  
  // 渲染进度组件
  const renderProgress = (progress: ProgressInfo) => (
    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{progress.message}</span>
        <span className="text-sm text-gray-600">{progress.percent}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress.percent}%` }}
        />
      </div>
      {progress.preview && (
        <div className="mt-3 p-3 bg-white rounded border text-sm">
          {renderPreview(progress.preview)}
        </div>
      )}
    </div>
  )
  
  // 渲染操作按钮
  const renderActions = (actions: MessageAction[]) => (
    <div className="mt-3 flex flex-wrap gap-2">
      {actions.map((action, index) => (
        <button
          key={index}
          onClick={action.onClick}
          disabled={action.disabled || isProcessing}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 
                     disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {action.label}
        </button>
      ))}
    </div>
  )
  
  return (
    <div className="flex flex-col h-full">
      {/* 对话历史区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div key={message.id} className={`flex ${
            message.type === 'user' ? 'justify-end' : 'justify-start'
          }`}>
            <div className={`max-w-[80%] rounded-lg p-4 ${
              message.type === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-900'
            }`}>
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.progress && renderProgress(message.progress)}
              {message.actions && renderActions(message.actions)}
            </div>
          </div>
        ))}
      </div>
      
      {/* 输入区域 */}
      <div className="border-t p-4">
        <ChatInput 
          onSend={handleSend}
          disabled={isProcessing}
          placeholder={getPlaceholder()}
        />
      </div>
    </div>
  )
}
```

### 4.2 工作流状态显示
```typescript
// 工作流状态指示器
const WorkflowIndicator: React.FC<{ workflow: WorkflowState }> = ({ workflow }) => {
  const stages = [
    { id: 'upload', name: '上传', icon: Upload },
    { id: 'summary', name: '摘要', icon: FileText },
    { id: 'index', name: '索引', icon: Search },
    { id: 'analysis', name: '分析', icon: Brain }
  ]
  
  return (
    <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
      {stages.map((stage, index) => {
        const status = getStageStatus(workflow, stage.id)
        const Icon = stage.icon
        
        return (
          <div key={stage.id} className="flex items-center">
            <div className={`
              flex items-center justify-center w-8 h-8 rounded-full
              ${status === 'completed' ? 'bg-green-500 text-white' : 
                status === 'active' ? 'bg-blue-500 text-white animate-pulse' :
                status === 'pending' ? 'bg-gray-300 text-gray-600' :
                'bg-red-500 text-white'}
            `}>
              <Icon size={16} />
            </div>
            <span className="ml-2 text-sm font-medium">{stage.name}</span>
            {index < stages.length - 1 && (
              <div className={`ml-2 w-8 h-0.5 ${
                status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
```

## 5. 使用示例

### 5.1 完整的对话流程
```python
# 用户上传文档后的完整对话流程示例

# 1. 文档上传完成，触发工作流
user: [上传文档: "AI医疗应用研究.pdf"]
chatbot: 📄 文档 "AI医疗应用研究.pdf" 已成功上传！
         文件大小：3.2MB，共52页
         
         我注意到这是一份研究报告，建议进行以下处理：
         1. 🔍 快速摘要 - 了解文档主要内容（约30秒）
         2. 📑 创建索引 - 支持精准搜索（约2分钟）
         3. 🧠 深度分析 - 提取关键洞察（约5分钟）
         
         您想从哪个开始？或者有其他需求？

# 2. 用户选择生成摘要
user: 先生成摘要，重点关注技术实现和应用案例

chatbot: 🚀 开始生成摘要...
         我会特别关注：技术实现、应用案例
         
         [进度: 20%] 正在解析文档结构...
         [进度: 40%] 正在提取关键章节...
         [进度: 60%] 正在分析技术实现部分...
         
         📊 已识别到的关键信息：
         - 文档类型：学术研究报告
         - 技术栈：TensorFlow, PyTorch
         - 应用领域：医学影像诊断、病理分析
         
         [进度: 80%] 正在整理应用案例...
         [进度: 100%] 
         
         ✅ 摘要生成完成！
         
         [显示摘要内容...]
         
         基于摘要内容，我建议：
         1. 创建技术术语索引，方便查找具体实现细节
         2. 深度分析各应用案例的成功因素
         
         您想继续哪个操作？

# 3. 用户中断并修改需求
user: 等一下，还要加上对比其他研究的内容

chatbot: ⏸️ 已暂停当前操作
         
         好的，我会在后续处理中加入对比分析。
         
         您是想：
         1. 重新生成包含对比内容的摘要
         2. 在现有摘要基础上补充对比分析
         3. 在深度分析阶段进行详细对比
         
         请选择您偏好的方式

# 4. 继续处理流程...
```

这个设计方案提供了一个完整的通过chatbot实现文档全生命周期管理的框架，包括了核心功能设计、技术架构和实现示例。你可以根据这个方案进行review，有任何需要调整或补充的地方请告诉我！