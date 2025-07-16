"""
记忆库(Memory Bank)管理器
基于文件系统的持久化记忆层，人类可读且易于维护
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from ...utils.logger import get_logger

logger = get_logger(__name__)


class MemoryBankManager:
    """记忆库管理器 - RVUE生命周期"""
    
    def __init__(self, base_path: str = "./memory-bank"):
        self.base_path = Path(base_path)
        self.ensure_structure()
        
    def ensure_structure(self):
        """确保记忆库目录结构存在"""
        directories = [
            "",  # 根目录
            "knowledge_graph",
            "knowledge_graph/visualizations",
            "learning_journal",
            "hypotheses",
            "research_plans",
            "research_plans/completed"
        ]
        
        for dir_path in directories:
            (self.base_path / dir_path).mkdir(parents=True, exist_ok=True)
        
        # 初始化元数据文件
        metadata_file = self.base_path / "metadata.json"
        if not metadata_file.exists():
            self._write_json(metadata_file, {
                "created_at": datetime.now().isoformat(),
                "version": "3.0",
                "description": "DPA认知系统记忆库"
            })
    
    async def read_verify_update_execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """RVUE生命周期 - 读取、验证、更新、执行"""
        
        # 1. Read - 读取记忆库
        memory_content = await self.read_all_memories()
        state["memory_bank_state"] = memory_content
        
        # 2. Verify - 验证一致性
        verification_result = await self.verify_consistency(
            memory_content, 
            state.get("knowledge_graph_snapshot", {})
        )
        
        if not verification_result["is_consistent"]:
            # 3. Reconcile - 调和差异
            state = await self.reconcile_differences(
                memory_content,
                state,
                verification_result["conflicts"]
            )
        
        # 4. Update - 更新记忆库（在工作流执行后）
        # Execute步骤由其他节点完成
        
        return state
    
    async def read_all_memories(self) -> Dict[str, Any]:
        """读取所有记忆内容"""
        memories = {
            "metadata": self._read_json(self.base_path / "metadata.json"),
            "source_documents": await self._read_markdown("source_documents.md"),
            "key_concepts": await self._read_markdown("key_concepts.md"),
            "dynamic_summary": await self._read_markdown("dynamic_summary.md"),
            "agent_rules": await self._read_markdown("agent_rules.md"),
            "knowledge_graph": {
                "snapshot": self._read_json(self.base_path / "knowledge_graph" / "graph_snapshot.json")
            },
            "learning_journal": await self._read_learning_journal(),
            "hypotheses": {
                "active": await self._read_markdown("hypotheses/active.md"),
                "verified": await self._read_markdown("hypotheses/verified.md"),
                "rejected": await self._read_markdown("hypotheses/rejected.md")
            },
            "research_plans": {
                "current": await self._read_markdown("research_plans/current_plan.md")
            }
        }
        
        return memories
    
    async def verify_consistency(
        self, 
        memory_content: Dict[str, Any],
        graph_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证记忆库与知识图谱的一致性"""
        conflicts = []
        
        # 1. 检查概念一致性
        memory_concepts = self._extract_concepts_from_memory(memory_content)
        graph_concepts = set(graph_snapshot.get("nodes", []))
        
        missing_in_graph = memory_concepts - graph_concepts
        missing_in_memory = graph_concepts - memory_concepts
        
        if missing_in_graph:
            conflicts.append({
                "type": "missing_concepts_in_graph",
                "concepts": list(missing_in_graph)
            })
        
        if missing_in_memory:
            conflicts.append({
                "type": "missing_concepts_in_memory",
                "concepts": list(missing_in_memory)
            })
        
        # 2. 检查时间戳一致性
        memory_timestamp = memory_content.get("metadata", {}).get("last_updated")
        graph_timestamp = graph_snapshot.get("timestamp")
        
        if memory_timestamp and graph_timestamp:
            if datetime.fromisoformat(memory_timestamp) < datetime.fromisoformat(graph_timestamp):
                conflicts.append({
                    "type": "outdated_memory",
                    "memory_time": memory_timestamp,
                    "graph_time": graph_timestamp
                })
        
        return {
            "is_consistent": len(conflicts) == 0,
            "conflicts": conflicts
        }
    
    async def reconcile_differences(
        self,
        memory_content: Dict[str, Any],
        state: Dict[str, Any],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """调和记忆库与系统状态的差异"""
        for conflict in conflicts:
            if conflict["type"] == "missing_concepts_in_graph":
                # 将记忆库中的概念添加到待处理列表
                for concept in conflict["concepts"]:
                    state["extracted_graph_documents"].append({
                        "id": f"reconcile_{concept}",
                        "name": concept,
                        "source": "memory_bank_reconciliation"
                    })
            
            elif conflict["type"] == "missing_concepts_in_memory":
                # 标记需要更新记忆库
                state["memory_bank_needs_update"] = True
                
            elif conflict["type"] == "outdated_memory":
                # 标记需要完整同步
                state["memory_bank_needs_sync"] = True
        
        return state
    
    async def update_memories(self, state: Dict[str, Any]) -> None:
        """更新记忆库内容"""
        project_id = state.get("project_id", "default")
        project_path = self.base_path / f"project_{project_id}"
        project_path.mkdir(exist_ok=True)
        
        # 更新各个组件
        await self.update_dynamic_summary(state)
        await self.update_key_concepts(state)
        await self.update_knowledge_graph(state)
        await self.update_learning_journal(state)
        await self.update_hypotheses(state)
        
        # 更新元数据
        metadata = self._read_json(project_path / "metadata.json") or {}
        metadata.update({
            "last_updated": datetime.now().isoformat(),
            "total_concepts": len(state.get("concept_embeddings", {})),
            "total_documents": len(state.get("current_documents", [])),
            "learning_progress": state.get("research_progress", {})
        })
        self._write_json(project_path / "metadata.json", metadata)
    
    async def update_dynamic_summary(self, state: Dict[str, Any]) -> None:
        """更新动态摘要 - 使用渐进式摘要技术"""
        project_id = state.get("project_id", "default")
        summary_path = self.base_path / f"project_{project_id}" / "dynamic_summary.md"
        
        current_summary = await self._read_markdown(f"project_{project_id}/dynamic_summary.md") or ""
        new_insights = state.get("new_insights", [])
        
        # 构建更新的摘要
        summary_content = f"""# 动态知识摘要

最后更新: {datetime.now().isoformat()}
版本: {state.get('summary_version', 1) + 1}

## 核心理解

{current_summary}

## 最新洞察

"""
        
        for insight in new_insights[-5:]:  # 最新5条
            summary_content += f"- {insight.get('content', '')}\n"
            summary_content += f"  - 置信度: {insight.get('confidence', 0):.2f}\n"
            summary_content += f"  - 时间: {insight.get('timestamp', '')}\n\n"
        
        # 添加统计信息
        summary_content += f"""
## 知识统计

- 总概念数: {len(state.get('concept_embeddings', {}))}
- 已验证假设: {len(state.get('verified_hypotheses', []))}
- 活跃假设: {len(state.get('learning_hypotheses', []))}
- 知识盲点: {len(state.get('knowledge_gaps', []))}
"""
        
        await self._write_markdown(f"project_{project_id}/dynamic_summary.md", summary_content)
    
    async def update_key_concepts(self, state: Dict[str, Any]) -> None:
        """更新关键概念文档"""
        project_id = state.get("project_id", "default")
        
        # 从状态中提取概念
        concepts_by_type = defaultdict(list)
        
        # 从语义记忆中提取
        for concept_id, concept_data in state.get("semantic_memory", {}).items():
            concept_type = concept_data.get("type", "general")
            concepts_by_type[concept_type].append(concept_data)
        
        # 生成Mermaid图
        mermaid_graph = self._generate_concept_graph(state)
        
        # 构建内容
        content = f"""# 关键概念和实体

最后更新: {datetime.now().isoformat()}

## 概念分类

"""
        
        for concept_type, concepts in concepts_by_type.items():
            content += f"\n### {concept_type}\n\n"
            for concept in sorted(concepts, key=lambda x: x.get("importance", 0), reverse=True)[:20]:
                confidence = concept.get("confidence", 0.5)
                content += f"- **{concept.get('name', 'Unknown')}** (置信度: {confidence:.2f})\n"
                if concept.get("definition"):
                    content += f"  - {concept['definition']}\n"
                if concept.get("properties"):
                    content += f"  - 属性: {', '.join(concept['properties'].keys())}\n"
        
        # 添加概念关系图
        content += f"\n## 概念关系图\n\n```mermaid\n{mermaid_graph}\n```\n"
        
        await self._write_markdown(f"project_{project_id}/key_concepts.md", content)
    
    async def update_knowledge_graph(self, state: Dict[str, Any]) -> None:
        """更新知识图谱快照"""
        project_id = state.get("project_id", "default")
        graph_path = self.base_path / f"project_{project_id}" / "knowledge_graph"
        graph_path.mkdir(exist_ok=True)
        
        # 保存图谱快照
        snapshot = state.get("knowledge_graph_snapshot", {})
        snapshot["timestamp"] = datetime.now().isoformat()
        snapshot["statistics"] = {
            "total_nodes": len(snapshot.get("nodes", [])),
            "total_edges": len(snapshot.get("edges", [])),
            "node_types": self._count_node_types(snapshot),
            "edge_types": self._count_edge_types(snapshot)
        }
        
        self._write_json(graph_path / "graph_snapshot.json", snapshot)
        
        # 生成可视化
        await self._generate_graph_visualizations(snapshot, graph_path / "visualizations")
    
    async def update_learning_journal(self, state: Dict[str, Any]) -> None:
        """更新学习日志"""
        project_id = state.get("project_id", "default")
        journal_path = self.base_path / f"project_{project_id}" / "learning_journal"
        journal_path.mkdir(exist_ok=True)
        
        # 按日期组织
        today = datetime.now().strftime("%Y-%m-%d")
        journal_file = journal_path / f"{today}.md"
        
        # 读取现有内容
        existing_content = ""
        if journal_file.exists():
            existing_content = journal_file.read_text(encoding="utf-8")
        
        # 追加新条目
        new_entry = f"""
## {datetime.now().strftime("%H:%M:%S")} - 学习记录

### 处理的文档
"""
        for doc in state.get("current_documents", [])[-3:]:  # 最近3个
            new_entry += f"- {doc.get('title', 'Untitled')}\n"
        
        new_entry += "\n### 发现的概念\n"
        for concept in state.get("new_concepts", [])[-5:]:  # 最近5个
            new_entry += f"- {concept}\n"
        
        new_entry += "\n### 生成的假设\n"
        for hypothesis in state.get("learning_hypotheses", [])[-3:]:  # 最近3个
            new_entry += f"- {hypothesis.get('content', '')}\n"
        
        new_entry += "\n### 识别的知识盲点\n"
        for gap in state.get("knowledge_gaps", [])[-3:]:  # 最近3个
            new_entry += f"- {gap.get('description', '')}\n"
        
        new_entry += "\n---\n"
        
        # 写入文件
        journal_file.write_text(existing_content + new_entry, encoding="utf-8")
    
    async def update_hypotheses(self, state: Dict[str, Any]) -> None:
        """更新假设管理"""
        project_id = state.get("project_id", "default")
        hypotheses_path = self.base_path / f"project_{project_id}" / "hypotheses"
        hypotheses_path.mkdir(exist_ok=True)
        
        # 活跃假设
        active_content = f"""# 活跃假设

最后更新: {datetime.now().isoformat()}

## 待验证假设

"""
        for hyp in state.get("learning_hypotheses", []):
            active_content += f"""
### {hyp.get('id', 'Unknown')}

**假设**: {hyp.get('content', '')}

- 置信度: {hyp.get('confidence', 0):.2f}
- 来源: {hyp.get('source', 'Unknown')}
- 创建时间: {hyp.get('created_at', '')}
- 验证方法: {hyp.get('verification_method', '待定')}

---
"""
        
        await self._write_markdown(f"project_{project_id}/hypotheses/active.md", active_content)
    
    # === 辅助方法 ===
    
    def _read_json(self, path: Path) -> Optional[Dict]:
        """读取JSON文件"""
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Error reading JSON {path}: {e}")
        return None
    
    def _write_json(self, path: Path, data: Dict) -> None:
        """写入JSON文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    async def _read_markdown(self, relative_path: str) -> Optional[str]:
        """读取Markdown文件"""
        path = self.base_path / relative_path
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
    
    async def _write_markdown(self, relative_path: str, content: str) -> None:
        """写入Markdown文件"""
        path = self.base_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    
    async def _read_learning_journal(self) -> Dict[str, str]:
        """读取学习日志"""
        journal_path = self.base_path / "learning_journal"
        journals = {}
        
        if journal_path.exists():
            for file_path in journal_path.glob("*.md"):
                journals[file_path.stem] = file_path.read_text(encoding="utf-8")
        
        return journals
    
    def _extract_concepts_from_memory(self, memory_content: Dict) -> set:
        """从记忆内容中提取概念"""
        concepts = set()
        
        # 从key_concepts中提取
        if memory_content.get("key_concepts"):
            # 这里应该解析Markdown内容提取概念
            pass
        
        # 从知识图谱中提取
        if memory_content.get("knowledge_graph", {}).get("snapshot", {}).get("nodes"):
            for node in memory_content["knowledge_graph"]["snapshot"]["nodes"]:
                concepts.add(node.get("name", node.get("id")))
        
        return concepts
    
    def _generate_concept_graph(self, state: Dict[str, Any]) -> str:
        """生成概念关系的Mermaid图"""
        graph_lines = ["graph TD"]
        
        # 简化版 - 实际应该基于关系生成
        concepts = list(state.get("semantic_memory", {}).keys())[:10]
        
        for i, concept in enumerate(concepts):
            safe_id = f"C{i}"
            graph_lines.append(f'    {safe_id}["{concept}"]')
        
        # 添加一些示例关系
        if len(concepts) > 1:
            graph_lines.append(f"    C0 --> C1")
        
        return "\n".join(graph_lines)
    
    def _count_node_types(self, snapshot: Dict) -> Dict[str, int]:
        """统计节点类型"""
        type_counts = defaultdict(int)
        for node in snapshot.get("nodes", []):
            node_type = node.get("type", "unknown")
            type_counts[node_type] += 1
        return dict(type_counts)
    
    def _count_edge_types(self, snapshot: Dict) -> Dict[str, int]:
        """统计边类型"""
        type_counts = defaultdict(int)
        for edge in snapshot.get("edges", []):
            edge_type = edge.get("type", "unknown")
            type_counts[edge_type] += 1
        return dict(type_counts)
    
    async def _generate_graph_visualizations(self, snapshot: Dict, viz_path: Path) -> None:
        """生成图谱可视化"""
        viz_path.mkdir(exist_ok=True)
        
        # 生成概览图
        overview = f"""# 知识图谱概览

生成时间: {datetime.now().isoformat()}

## 统计信息

- 节点总数: {snapshot['statistics']['total_nodes']}
- 边总数: {snapshot['statistics']['total_edges']}

## 节点类型分布

"""
        for node_type, count in snapshot['statistics']['node_types'].items():
            overview += f"- {node_type}: {count}\n"
        
        overview += "\n## 关系类型分布\n\n"
        for edge_type, count in snapshot['statistics']['edge_types'].items():
            overview += f"- {edge_type}: {count}\n"
        
        (viz_path / "overview.md").write_text(overview, encoding="utf-8")


# 工厂函数
def create_memory_bank_manager(base_path: str = "./memory-bank") -> MemoryBankManager:
    """创建记忆库管理器实例"""
    return MemoryBankManager(base_path)