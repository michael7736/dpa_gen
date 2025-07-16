"""
Memory Bank管理器 - 持久化记忆存储
实现CRUD操作、动态摘要、关键概念管理和学习日志
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import aiofiles
from dataclasses import dataclass, asdict
import re

from src.config.settings import settings
from src.utils.logging_utils import get_logger
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = get_logger(__name__)

# 默认配置
DEFAULT_USER_ID = "u1"
MAX_CONTEXT_SIZE = 10 * 1024  # 10KB
MAX_SUMMARY_SIZE = 5 * 1024    # 5KB
MAX_CONCEPTS = 100
MAX_JOURNAL_ENTRIES = 1000


@dataclass
class MemoryBankMetadata:
    """Memory Bank元数据"""
    project_id: str
    user_id: str
    created_at: str
    updated_at: str
    version: str = "1.0.0"
    stats: Dict[str, int] = None
    
    def __post_init__(self):
        if self.stats is None:
            self.stats = {
                "total_interactions": 0,
                "total_concepts": 0,
                "total_documents": 0,
                "context_updates": 0
            }


@dataclass
class Concept:
    """概念定义"""
    name: str
    category: str
    description: str
    confidence: float = 1.0
    first_seen: str = None
    last_seen: str = None
    frequency: int = 1
    relationships: List[str] = None
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = datetime.now().isoformat()
        if self.last_seen is None:
            self.last_seen = self.first_seen
        if self.relationships is None:
            self.relationships = []


@dataclass
class JournalEntry:
    """学习日志条目"""
    timestamp: str
    event_type: str  # "learn", "forget", "reinforce", "connect"
    content: str
    metadata: Dict[str, Any] = None
    impact_score: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class MemoryBankManager:
    """
    Memory Bank管理器
    负责管理项目的持久化记忆
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        self.base_path = Path(settings.paths.memory_bank)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # LLM用于生成摘要
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # 使用OpenAI模型
            temperature=0.3,
            api_key=settings.ai_model.openai_api_key
        )
        
        # 文件锁（简单实现）
        self._locks: Dict[str, asyncio.Lock] = {}
        
    def _get_project_path(self, project_id: str) -> Path:
        """获取项目路径（支持用户隔离）"""
        if self.user_id == DEFAULT_USER_ID:
            return self.base_path / f"project_{project_id}"
        else:
            return self.base_path / self.user_id / f"project_{project_id}"
            
    async def _acquire_lock(self, key: str) -> asyncio.Lock:
        """获取文件锁"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
        
    async def initialize_project(self, project_id: str) -> bool:
        """初始化项目Memory Bank"""
        project_path = self._get_project_path(project_id)
        
        try:
            # 创建目录结构
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "learning_journal").mkdir(exist_ok=True)
            (project_path / "snapshots").mkdir(exist_ok=True)
            
            # 创建元数据
            metadata = MemoryBankMetadata(
                project_id=project_id,
                user_id=self.user_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # 创建初始文件
            await self._write_json(
                project_path / "metadata.json",
                asdict(metadata)
            )
            
            await self._write_file(
                project_path / "context.md",
                f"# Project Context - {project_id}\n\n*Initialized at {metadata.created_at}*\n\n"
            )
            
            await self._write_file(
                project_path / "summary.md",
                f"# Project Summary - {project_id}\n\n## Overview\n\nThis project was initialized on {metadata.created_at}.\n\n"
            )
            
            await self._write_json(
                project_path / "concepts.json",
                []
            )
            
            # 创建初始学习日志
            journal_entry = JournalEntry(
                timestamp=datetime.now().isoformat(),
                event_type="learn",
                content=f"Project {project_id} initialized",
                metadata={"action": "initialize"}
            )
            
            await self._append_journal(project_path, journal_entry)
            
            logger.info(f"Initialized Memory Bank for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Memory Bank: {e}")
            return False
            
    async def update_context(
        self, 
        project_id: str, 
        new_content: str,
        source: Optional[str] = None
    ) -> bool:
        """更新项目上下文（FIFO策略保持大小）"""
        project_path = self._get_project_path(project_id)
        context_path = project_path / "context.md"
        
        lock = await self._acquire_lock(f"{project_id}:context")
        
        async with lock:
            try:
                # 读取现有内容
                current_content = await self._read_file(context_path)
                
                # 添加新内容
                timestamp = datetime.now().isoformat()
                new_section = f"\n\n## {timestamp}"
                if source:
                    new_section += f" - Source: {source}"
                new_section += f"\n\n{new_content}\n"
                
                updated_content = current_content + new_section
                
                # 如果超过大小限制，从开头截断
                if len(updated_content) > MAX_CONTEXT_SIZE:
                    # 保留标题行
                    lines = updated_content.split('\n')
                    header = []
                    content_start = 0
                    
                    for i, line in enumerate(lines):
                        if line.startswith('# '):
                            header.append(line)
                            content_start = i + 1
                        else:
                            break
                            
                    # 计算需要保留的内容
                    header_text = '\n'.join(header) + '\n\n'
                    remaining_size = MAX_CONTEXT_SIZE - len(header_text) - len(new_section)
                    
                    # 从后向前保留内容
                    body = '\n'.join(lines[content_start:])
                    if len(body) > remaining_size:
                        body = '...\n\n' + body[-remaining_size:]
                        
                    updated_content = header_text + body + new_section
                    
                # 写入更新内容
                await self._write_file(context_path, updated_content)
                
                # 更新元数据
                await self._update_metadata(project_id, {"context_updates": 1})
                
                # 记录学习日志
                journal_entry = JournalEntry(
                    timestamp=timestamp,
                    event_type="learn",
                    content=f"Context updated with {len(new_content)} characters",
                    metadata={"source": source, "size": len(new_content)}
                )
                await self._append_journal(project_path, journal_entry)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to update context: {e}")
                return False
                
    async def add_concepts(
        self, 
        project_id: str, 
        new_concepts: List[Dict[str, Any]]
    ) -> int:
        """添加新概念（自动去重和更新）"""
        project_path = self._get_project_path(project_id)
        concepts_path = project_path / "concepts.json"
        
        lock = await self._acquire_lock(f"{project_id}:concepts")
        
        async with lock:
            try:
                # 读取现有概念
                existing_data = await self._read_json(concepts_path)
                concepts_dict = {c["name"]: Concept(**c) for c in existing_data}
                
                added_count = 0
                updated_count = 0
                
                for concept_data in new_concepts:
                    concept_name = concept_data.get("name")
                    if not concept_name:
                        continue
                        
                    if concept_name in concepts_dict:
                        # 更新现有概念
                        existing = concepts_dict[concept_name]
                        existing.frequency += 1
                        existing.last_seen = datetime.now().isoformat()
                        
                        # 合并关系
                        new_relations = concept_data.get("relationships", [])
                        for rel in new_relations:
                            if rel not in existing.relationships:
                                existing.relationships.append(rel)
                                
                        updated_count += 1
                    else:
                        # 添加新概念
                        new_concept = Concept(
                            name=concept_name,
                            category=concept_data.get("category", "general"),
                            description=concept_data.get("description", ""),
                            confidence=concept_data.get("confidence", 1.0),
                            relationships=concept_data.get("relationships", [])
                        )
                        concepts_dict[concept_name] = new_concept
                        added_count += 1
                        
                # 限制概念数量
                if len(concepts_dict) > MAX_CONCEPTS:
                    # 按频率和最后访问时间排序，保留最重要的
                    sorted_concepts = sorted(
                        concepts_dict.values(),
                        key=lambda c: (c.frequency, c.last_seen),
                        reverse=True
                    )
                    concepts_dict = {c.name: c for c in sorted_concepts[:MAX_CONCEPTS]}
                    
                # 保存更新后的概念
                concepts_list = [asdict(c) for c in concepts_dict.values()]
                await self._write_json(concepts_path, concepts_list)
                
                # 更新元数据
                await self._update_metadata(
                    project_id, 
                    {"total_concepts": len(concepts_dict)}
                )
                
                # 记录学习日志
                if added_count > 0 or updated_count > 0:
                    journal_entry = JournalEntry(
                        timestamp=datetime.now().isoformat(),
                        event_type="learn",
                        content=f"Added {added_count} new concepts, updated {updated_count}",
                        metadata={
                            "added": added_count,
                            "updated": updated_count,
                            "total": len(concepts_dict)
                        }
                    )
                    await self._append_journal(project_path, journal_entry)
                    
                return added_count
                
            except Exception as e:
                logger.error(f"Failed to add concepts: {e}")
                return 0
                
    async def update_summary(
        self, 
        project_id: str,
        force_regenerate: bool = False
    ) -> str:
        """更新项目摘要（智能生成）"""
        project_path = self._get_project_path(project_id)
        summary_path = project_path / "summary.md"
        
        lock = await self._acquire_lock(f"{project_id}:summary")
        
        async with lock:
            try:
                # 读取必要信息
                metadata = await self._read_json(project_path / "metadata.json")
                context = await self._read_file(project_path / "context.md")
                concepts_data = await self._read_json(project_path / "concepts.json")
                current_summary = await self._read_file(summary_path)
                
                # 检查是否需要更新
                if not force_regenerate:
                    # 简单策略：如果最近更新过，跳过
                    last_update = datetime.fromisoformat(metadata.get("updated_at", "2000-01-01"))
                    if (datetime.now() - last_update).seconds < 300:  # 5分钟内
                        return current_summary
                        
                # 准备摘要生成的输入
                concepts = [Concept(**c) for c in concepts_data]
                top_concepts = sorted(concepts, key=lambda c: c.frequency, reverse=True)[:20]
                
                # 生成摘要
                summary_prompt = ChatPromptTemplate.from_messages([
                    ("system", """你是一个专业的知识管理助手。请基于提供的信息生成项目摘要。
                    要求：
                    1. 概述项目的主要内容和目标
                    2. 总结关键概念和主题
                    3. 分析知识结构和关联
                    4. 提供学习进展评估
                    保持简洁，使用Markdown格式。"""),
                    ("human", """
                    项目信息：
                    - 项目ID: {project_id}
                    - 创建时间: {created_at}
                    - 总交互次数: {total_interactions}
                    - 概念数量: {total_concepts}
                    
                    最近上下文（最后500字）:
                    {recent_context}
                    
                    主要概念:
                    {concepts_list}
                    
                    当前摘要:
                    {current_summary}
                    
                    请生成更新的项目摘要。
                    """)
                ])
                
                # 准备变量
                recent_context = context[-500:] if len(context) > 500 else context
                concepts_list = "\n".join([
                    f"- {c.name} ({c.category}): {c.description[:50]}... [频率: {c.frequency}]"
                    for c in top_concepts
                ])
                
                # 调用LLM生成摘要
                response = await self.llm.ainvoke(
                    summary_prompt.format_messages(
                        project_id=project_id,
                        created_at=metadata.get("created_at", "Unknown"),
                        total_interactions=metadata.get("stats", {}).get("total_interactions", 0),
                        total_concepts=len(concepts),
                        recent_context=recent_context,
                        concepts_list=concepts_list,
                        current_summary=current_summary[-1000:]  # 只提供最近的部分
                    )
                )
                
                new_summary = response.content
                
                # 确保不超过大小限制
                if len(new_summary) > MAX_SUMMARY_SIZE:
                    new_summary = new_summary[:MAX_SUMMARY_SIZE-100] + "\n\n...[Truncated]"
                    
                # 保存摘要
                await self._write_file(summary_path, new_summary)
                
                # 记录日志
                journal_entry = JournalEntry(
                    timestamp=datetime.now().isoformat(),
                    event_type="reinforce",
                    content="Summary regenerated",
                    metadata={"size": len(new_summary), "forced": force_regenerate}
                )
                await self._append_journal(project_path, journal_entry)
                
                return new_summary
                
            except Exception as e:
                logger.error(f"Failed to update summary: {e}")
                return current_summary
                
    async def get_snapshot(self, project_id: str) -> Dict[str, Any]:
        """获取项目记忆快照"""
        project_path = self._get_project_path(project_id)
        
        if not project_path.exists():
            return {}
            
        try:
            # 读取所有必要文件
            metadata = await self._read_json(project_path / "metadata.json")
            context = await self._read_file(project_path / "context.md")
            summary = await self._read_file(project_path / "summary.md")
            concepts = await self._read_json(project_path / "concepts.json")
            
            # 获取最近的学习日志
            recent_journal = await self._get_recent_journal_entries(project_path, limit=10)
            
            return {
                "project_id": project_id,
                "user_id": self.user_id,
                "metadata": metadata,
                "context_preview": context[:500] + "..." if len(context) > 500 else context,
                "context_size": len(context),
                "summary": summary,
                "concepts_count": len(concepts),
                "top_concepts": sorted(
                    concepts, 
                    key=lambda c: c.get("frequency", 0), 
                    reverse=True
                )[:10],
                "recent_activities": recent_journal,
                "last_updated": metadata.get("updated_at", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Failed to get snapshot: {e}")
            return {}
            
    async def search_concepts(
        self, 
        project_id: str, 
        query: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索概念"""
        project_path = self._get_project_path(project_id)
        concepts_path = project_path / "concepts.json"
        
        try:
            concepts_data = await self._read_json(concepts_path)
            concepts = [Concept(**c) for c in concepts_data]
            
            # 过滤和搜索
            results = []
            query_lower = query.lower()
            
            for concept in concepts:
                # 类别过滤
                if category and concept.category != category:
                    continue
                    
                # 文本匹配
                if (query_lower in concept.name.lower() or 
                    query_lower in concept.description.lower()):
                    results.append(asdict(concept))
                    
            # 按相关性排序
            results.sort(key=lambda c: c["frequency"], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search concepts: {e}")
            return []
            
    async def export_memory(self, project_id: str) -> Dict[str, Any]:
        """导出完整记忆"""
        project_path = self._get_project_path(project_id)
        
        if not project_path.exists():
            return {}
            
        try:
            # 读取所有数据
            metadata = await self._read_json(project_path / "metadata.json")
            context = await self._read_file(project_path / "context.md")
            summary = await self._read_file(project_path / "summary.md")
            concepts = await self._read_json(project_path / "concepts.json")
            
            # 读取完整学习日志
            all_journal = await self._get_all_journal_entries(project_path)
            
            return {
                "export_timestamp": datetime.now().isoformat(),
                "project_id": project_id,
                "user_id": self.user_id,
                "metadata": metadata,
                "context": context,
                "summary": summary,
                "concepts": concepts,
                "learning_journal": all_journal,
                "statistics": {
                    "total_concepts": len(concepts),
                    "journal_entries": len(all_journal),
                    "context_size": len(context),
                    "summary_size": len(summary)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to export memory: {e}")
            return {}
            
    async def _write_file(self, path: Path, content: str):
        """写入文件"""
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(content)
            
    async def _read_file(self, path: Path) -> str:
        """读取文件"""
        if not path.exists():
            return ""
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return await f.read()
            
    async def _write_json(self, path: Path, data: Any):
        """写入JSON文件"""
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
    async def _read_json(self, path: Path) -> Any:
        """读取JSON文件"""
        if not path.exists():
            return {} if path.name == "metadata.json" else []
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content) if content else ({} if path.name == "metadata.json" else [])
            
    async def _update_metadata(self, project_id: str, updates: Dict[str, Any]):
        """更新元数据"""
        project_path = self._get_project_path(project_id)
        metadata_path = project_path / "metadata.json"
        
        metadata = await self._read_json(metadata_path)
        metadata["updated_at"] = datetime.now().isoformat()
        
        # 更新统计信息
        if "stats" not in metadata:
            metadata["stats"] = {}
            
        for key, value in updates.items():
            if key in ["context_updates", "total_interactions"]:
                metadata["stats"][key] = metadata["stats"].get(key, 0) + value
            else:
                metadata["stats"][key] = value
                
        await self._write_json(metadata_path, metadata)
        
    async def _append_journal(self, project_path: Path, entry: JournalEntry):
        """追加学习日志"""
        journal_dir = project_path / "learning_journal"
        journal_dir.mkdir(exist_ok=True)
        
        # 按日期组织日志文件
        date_str = datetime.now().strftime("%Y%m%d")
        journal_file = journal_dir / f"{date_str}.jsonl"
        
        async with aiofiles.open(journal_file, 'a', encoding='utf-8') as f:
            await f.write(json.dumps(asdict(entry), ensure_ascii=False) + '\n')
            
        # 清理旧日志（保留最近30天）
        await self._cleanup_old_journals(journal_dir)
        
    async def _get_recent_journal_entries(
        self, 
        project_path: Path, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近的学习日志"""
        journal_dir = project_path / "learning_journal"
        if not journal_dir.exists():
            return []
            
        entries = []
        
        # 按日期倒序读取文件
        journal_files = sorted(journal_dir.glob("*.jsonl"), reverse=True)
        
        for journal_file in journal_files:
            if len(entries) >= limit:
                break
                
            async with aiofiles.open(journal_file, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
                for line in reversed(lines):
                    if len(entries) >= limit:
                        break
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except:
                        continue
                        
        return entries
        
    async def _get_all_journal_entries(self, project_path: Path) -> List[Dict[str, Any]]:
        """获取所有学习日志"""
        journal_dir = project_path / "learning_journal"
        if not journal_dir.exists():
            return []
            
        entries = []
        
        # 按日期顺序读取文件
        journal_files = sorted(journal_dir.glob("*.jsonl"))
        
        for journal_file in journal_files:
            async with aiofiles.open(journal_file, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
                for line in lines:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except:
                        continue
                        
        return entries
        
    async def _cleanup_old_journals(self, journal_dir: Path, days_to_keep: int = 30):
        """清理旧的日志文件"""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for journal_file in journal_dir.glob("*.jsonl"):
            try:
                # 从文件名提取日期
                date_str = journal_file.stem
                file_date = datetime.strptime(date_str, "%Y%m%d").timestamp()
                
                if file_date < cutoff_date:
                    journal_file.unlink()
                    logger.info(f"Cleaned up old journal file: {journal_file}")
            except:
                continue


# 工厂函数
def create_memory_bank_manager(user_id: str = DEFAULT_USER_ID) -> MemoryBankManager:
    """创建Memory Bank管理器实例"""
    return MemoryBankManager(user_id=user_id)