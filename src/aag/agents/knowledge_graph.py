"""
Knowledge Graph Agent - 知识图谱构建Agent
从文档中提取实体和关系，构建知识图谱
"""

import json
import time
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from langchain_core.messages import HumanMessage, SystemMessage
from .base import BaseAgent
from ..prompts.templates import get_prompt_template
from ...utils.logger import get_logger

logger = get_logger(__name__)


class EntityType(Enum):
    """实体类型枚举"""
    PERSON = "person"           # 人物
    ORGANIZATION = "organization"  # 组织
    CONCEPT = "concept"         # 概念
    TECHNOLOGY = "technology"   # 技术
    LOCATION = "location"       # 地点
    EVENT = "event"            # 事件
    PRODUCT = "product"        # 产品
    OTHER = "other"            # 其他


class RelationType(Enum):
    """关系类型枚举"""
    DEFINES = "defines"         # 定义
    CONTAINS = "contains"       # 包含
    INFLUENCES = "influences"   # 影响
    CONTRASTS = "contrasts"     # 对比
    USES = "uses"              # 使用
    CREATES = "creates"        # 创建
    BELONGS_TO = "belongs_to"  # 属于
    RELATED_TO = "related_to"  # 相关


class KnowledgeGraphAgent(BaseAgent):
    """知识图谱构建Agent"""
    
    def __init__(self, **kwargs):
        super().__init__(name="KnowledgeGraphAgent", temperature=0.1, **kwargs)
        self.entity_cache = {}  # 实体缓存
        self.relation_cache = {}  # 关系缓存
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建知识图谱
        
        Args:
            input_data: 包含document_content、extraction_mode等
            context: 上下文信息
            
        Returns:
            知识图谱结果
        """
        start_time = time.time()
        
        try:
            # 验证输入
            if not await self.validate_input(input_data):
                raise ValueError("Invalid input data")
            
            document_content = input_data["document_content"]
            extraction_mode = input_data.get("extraction_mode", "comprehensive")
            document_id = input_data.get("document_id")
            
            # 获取缓存键
            cache_key = f"{document_id}_{extraction_mode}"
            
            # 检查缓存
            if cache_key in self.entity_cache and cache_key in self.relation_cache:
                logger.info(f"Using cached knowledge graph for {cache_key}")
                return {
                    "success": True,
                    "result": {
                        "entities": self.entity_cache[cache_key],
                        "relations": self.relation_cache[cache_key],
                        "statistics": self._calculate_statistics(
                            self.entity_cache[cache_key],
                            self.relation_cache[cache_key]
                        )
                    },
                    "metadata": {
                        "agent": self.name,
                        "duration": 0,
                        "tokens_used": 0,
                        "from_cache": True,
                        "extraction_mode": extraction_mode
                    }
                }
            
            # 根据模式提取实体和关系
            if extraction_mode == "quick":
                entities, relations = await self._quick_extraction(document_content)
            elif extraction_mode == "focused":
                focus_types = input_data.get("focus_types", ["concept", "technology"])
                entities, relations = await self._focused_extraction(
                    document_content, focus_types
                )
            else:  # comprehensive
                entities, relations = await self._comprehensive_extraction(document_content)
            
            # 后处理：去重、标准化、验证
            entities = self._postprocess_entities(entities)
            relations = self._postprocess_relations(relations, entities)
            
            # 计算统计信息
            statistics = self._calculate_statistics(entities, relations)
            
            # 缓存结果
            if document_id:
                self.entity_cache[cache_key] = entities
                self.relation_cache[cache_key] = relations
            
            # 计算token使用量
            tokens_used = self._estimate_tokens(document_content, entities, relations)
            
            # 记录性能指标
            end_time = time.time()
            self.log_metrics(start_time, end_time, tokens_used, True)
            
            # 更新上下文
            if context:
                context = self.update_context(context, {
                    "knowledge_graph_built": True,
                    "entity_count": len(entities),
                    "relation_count": len(relations)
                })
            
            return {
                "success": True,
                "result": {
                    "entities": entities,
                    "relations": relations,
                    "statistics": statistics
                },
                "metadata": {
                    "agent": self.name,
                    "duration": end_time - start_time,
                    "tokens_used": tokens_used,
                    "extraction_mode": extraction_mode,
                    "from_cache": False
                }
            }
            
        except Exception as e:
            logger.error(f"Error in KnowledgeGraphAgent: {str(e)}", exc_info=True)
            end_time = time.time()
            self.log_metrics(start_time, end_time, 0, False)
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "agent": self.name,
                    "duration": end_time - start_time
                }
            }
    
    async def _quick_extraction(
        self, document_content: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """快速提取模式：只提取最重要的实体和关系"""
        # 限制内容长度
        max_length = 8000
        if len(document_content) > max_length:
            document_content = document_content[:max_length] + "\n\n[内容已截断...]"
        
        prompt_template = get_prompt_template("knowledge_graph")
        prompt = prompt_template.format(document_content=document_content)
        
        messages = [
            SystemMessage(content="你是一位知识图谱专家，擅长从文本中快速提取核心实体和关系。"),
            HumanMessage(content=prompt + "\n\n注意：这是快速提取模式，请只提取最重要的5-10个实体和关系。")
        ]
        
        response = await self.llm.agenerate([messages])
        result_text = response.generations[0][0].text.strip()
        
        # 解析结果
        return self._parse_extraction_result(result_text)
    
    async def _focused_extraction(
        self, document_content: str, focus_types: List[str]
    ) -> Tuple[List[Dict], List[Dict]]:
        """聚焦提取模式：只提取特定类型的实体"""
        prompt_template = get_prompt_template("knowledge_graph")
        prompt = prompt_template.format(document_content=document_content)
        
        focus_instruction = f"\n\n注意：请聚焦于以下类型的实体：{', '.join(focus_types)}"
        
        messages = [
            SystemMessage(content="你是一位知识图谱专家，擅长精准提取特定类型的实体和关系。"),
            HumanMessage(content=prompt + focus_instruction)
        ]
        
        response = await self.llm.agenerate([messages])
        result_text = response.generations[0][0].text.strip()
        
        # 解析结果
        entities, relations = self._parse_extraction_result(result_text)
        
        # 过滤聚焦类型
        filtered_entities = [
            e for e in entities if e.get("type") in focus_types
        ]
        
        # 过滤相关关系
        entity_ids = {e["id"] for e in filtered_entities}
        filtered_relations = [
            r for r in relations 
            if r["source"] in entity_ids or r["target"] in entity_ids
        ]
        
        return filtered_entities, filtered_relations
    
    async def _comprehensive_extraction(
        self, document_content: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """全面提取模式：分段提取，合并结果"""
        # 分段处理长文档
        chunk_size = 8000
        chunks = self._split_document(document_content, chunk_size)
        
        all_entities = []
        all_relations = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            prompt_template = get_prompt_template("knowledge_graph")
            prompt = prompt_template.format(document_content=chunk)
            
            messages = [
                SystemMessage(content="你是一位知识图谱专家，擅长全面深入地提取实体和关系。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.agenerate([messages])
            result_text = response.generations[0][0].text.strip()
            
            # 解析结果
            entities, relations = self._parse_extraction_result(result_text)
            
            # 添加chunk标记
            for entity in entities:
                entity["chunk_id"] = i
            for relation in relations:
                relation["chunk_id"] = i
            
            all_entities.extend(entities)
            all_relations.extend(relations)
        
        return all_entities, all_relations
    
    def _split_document(self, document: str, chunk_size: int) -> List[str]:
        """将文档分割成多个chunk"""
        chunks = []
        words = document.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _parse_extraction_result(self, result_text: str) -> Tuple[List[Dict], List[Dict]]:
        """解析LLM返回的提取结果"""
        try:
            # 尝试直接解析JSON
            result = json.loads(result_text)
            return result.get("entities", []), result.get("relations", [])
        except json.JSONDecodeError:
            # 如果不是有效的JSON，尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return result.get("entities", []), result.get("relations", [])
                except:
                    pass
            
            logger.warning("Failed to parse extraction result as JSON")
            return [], []
    
    def _postprocess_entities(self, entities: List[Dict]) -> List[Dict]:
        """后处理实体：去重、标准化、添加ID"""
        # 去重
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # 使用名称和类型作为唯一标识
            key = (entity.get("name", "").lower(), entity.get("type", ""))
            if key not in seen:
                seen.add(key)
                
                # 标准化实体
                processed_entity = {
                    "id": f"entity_{len(unique_entities)+1}",
                    "name": entity.get("name", ""),
                    "type": self._normalize_entity_type(entity.get("type", "other")),
                    "attributes": entity.get("attributes", {})
                }
                
                # 添加默认属性
                if "importance" not in processed_entity["attributes"]:
                    processed_entity["attributes"]["importance"] = "medium"
                if "frequency" not in processed_entity["attributes"]:
                    processed_entity["attributes"]["frequency"] = 1
                
                unique_entities.append(processed_entity)
            else:
                # 增加频次
                for e in unique_entities:
                    if e["name"].lower() == entity.get("name", "").lower():
                        e["attributes"]["frequency"] += 1
                        break
        
        return unique_entities
    
    def _postprocess_relations(
        self, relations: List[Dict], entities: List[Dict]
    ) -> List[Dict]:
        """后处理关系：验证、标准化、添加权重"""
        # 创建实体名称到ID的映射
        entity_map = {e["name"].lower(): e["id"] for e in entities}
        
        processed_relations = []
        for relation in relations:
            source = relation.get("source", "").lower()
            target = relation.get("target", "").lower()
            
            # 验证实体是否存在
            if source in entity_map and target in entity_map:
                processed_relation = {
                    "source": entity_map[source],
                    "target": entity_map[target],
                    "type": self._normalize_relation_type(relation.get("type", "related_to")),
                    "weight": relation.get("weight", 0.5)
                }
                processed_relations.append(processed_relation)
        
        return processed_relations
    
    def _normalize_entity_type(self, type_str: str) -> str:
        """标准化实体类型"""
        type_str = type_str.lower()
        
        # 映射到标准类型
        type_mapping = {
            "人物": EntityType.PERSON.value,
            "人员": EntityType.PERSON.value,
            "组织": EntityType.ORGANIZATION.value,
            "机构": EntityType.ORGANIZATION.value,
            "公司": EntityType.ORGANIZATION.value,
            "概念": EntityType.CONCEPT.value,
            "理论": EntityType.CONCEPT.value,
            "技术": EntityType.TECHNOLOGY.value,
            "工具": EntityType.TECHNOLOGY.value,
            "算法": EntityType.TECHNOLOGY.value,
            "地点": EntityType.LOCATION.value,
            "地方": EntityType.LOCATION.value,
            "事件": EntityType.EVENT.value,
            "产品": EntityType.PRODUCT.value,
        }
        
        # 英文映射
        for entity_type in EntityType:
            if type_str == entity_type.value:
                return entity_type.value
        
        # 中文映射
        for key, value in type_mapping.items():
            if key in type_str:
                return value
        
        return EntityType.OTHER.value
    
    def _normalize_relation_type(self, type_str: str) -> str:
        """标准化关系类型"""
        type_str = type_str.lower()
        
        # 映射到标准类型
        type_mapping = {
            "定义": RelationType.DEFINES.value,
            "包含": RelationType.CONTAINS.value,
            "影响": RelationType.INFLUENCES.value,
            "对比": RelationType.CONTRASTS.value,
            "使用": RelationType.USES.value,
            "创建": RelationType.CREATES.value,
            "属于": RelationType.BELONGS_TO.value,
            "相关": RelationType.RELATED_TO.value,
        }
        
        # 英文映射
        for relation_type in RelationType:
            if type_str == relation_type.value:
                return relation_type.value
        
        # 中文映射
        for key, value in type_mapping.items():
            if key in type_str:
                return value
        
        return RelationType.RELATED_TO.value
    
    def _calculate_statistics(
        self, entities: List[Dict], relations: List[Dict]
    ) -> Dict[str, Any]:
        """计算知识图谱统计信息"""
        # 实体类型分布
        entity_type_dist = {}
        for entity in entities:
            entity_type = entity.get("type", "other")
            entity_type_dist[entity_type] = entity_type_dist.get(entity_type, 0) + 1
        
        # 关系类型分布
        relation_type_dist = {}
        for relation in relations:
            relation_type = relation.get("type", "related_to")
            relation_type_dist[relation_type] = relation_type_dist.get(relation_type, 0) + 1
        
        # 计算节点度
        node_degrees = {}
        for relation in relations:
            source = relation["source"]
            target = relation["target"]
            node_degrees[source] = node_degrees.get(source, 0) + 1
            node_degrees[target] = node_degrees.get(target, 0) + 1
        
        # 找出核心节点（度数最高的前5个）
        top_nodes = sorted(
            node_degrees.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 获取核心实体名称
        entity_id_to_name = {e["id"]: e["name"] for e in entities}
        core_entities = [
            {
                "name": entity_id_to_name.get(node_id, node_id),
                "degree": degree
            }
            for node_id, degree in top_nodes
        ]
        
        return {
            "total_entities": len(entities),
            "total_relations": len(relations),
            "entity_type_distribution": entity_type_dist,
            "relation_type_distribution": relation_type_dist,
            "core_entities": core_entities,
            "average_node_degree": sum(node_degrees.values()) / len(node_degrees) if node_degrees else 0
        }
    
    def _estimate_tokens(
        self, content: str, entities: List[Dict], relations: List[Dict]
    ) -> int:
        """估算token使用量"""
        # 简单估算：每4个字符约1个token
        input_tokens = len(content) // 4
        output_tokens = (len(str(entities)) + len(str(relations))) // 4
        return input_tokens + output_tokens
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ["document_content"]
        
        for field in required_fields:
            if field not in input_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        if not input_data["document_content"] or len(input_data["document_content"]) < 10:
            logger.error("Document content is empty or too short")
            return False
        
        # 验证提取模式
        if "extraction_mode" in input_data:
            valid_modes = ["quick", "focused", "comprehensive"]
            if input_data["extraction_mode"] not in valid_modes:
                logger.error(f"Invalid extraction mode: {input_data['extraction_mode']}")
                return False
        
        return True
    
    async def export_to_neo4j_format(
        self, entities: List[Dict], relations: List[Dict]
    ) -> Dict[str, Any]:
        """导出为Neo4j可导入的格式"""
        # 创建节点语句
        node_statements = []
        for entity in entities:
            props = {
                "name": entity["name"],
                "type": entity["type"],
                **entity.get("attributes", {})
            }
            props_str = ", ".join([f"{k}: '{v}'" for k, v in props.items()])
            statement = f"CREATE (n:{entity['type'].title()} {{{props_str}}})"
            node_statements.append(statement)
        
        # 创建关系语句
        edge_statements = []
        entity_id_to_name = {e["id"]: e["name"] for e in entities}
        
        for relation in relations:
            source_name = entity_id_to_name[relation["source"]]
            target_name = entity_id_to_name[relation["target"]]
            rel_type = relation["type"].upper()
            
            statement = f"""
            MATCH (a {{name: '{source_name}'}}), (b {{name: '{target_name}'}})
            CREATE (a)-[:{rel_type} {{weight: {relation['weight']}}}]->(b)
            """
            edge_statements.append(statement.strip())
        
        return {
            "node_statements": node_statements,
            "edge_statements": edge_statements,
            "cypher_script": "\n".join(node_statements + edge_statements)
        }