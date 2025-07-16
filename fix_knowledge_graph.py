#!/usr/bin/env python3
"""
修复知识图谱生成问题的补丁
"""

import json
import re
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage


def create_improved_entity_extraction_prompt(text: str) -> str:
    """创建改进的实体提取提示"""
    return f"""
请从以下文本中提取命名实体。

文本内容：
{text[:1000]}

要求：
1. 识别人物（Person）、组织（Organization）、地点（Location）、概念（Concept）、技术（Technology）等实体
2. 返回JSON格式的列表，每个实体包含：
   - name: 实体名称
   - type: 实体类型（Person/Organization/Location/Concept/Technology）
   - importance: 重要性（0-1之间的小数）

请确保返回有效的JSON格式，例如：
[
    {{"name": "OpenAI", "type": "Organization", "importance": 0.9}},
    {{"name": "GPT-4", "type": "Technology", "importance": 0.8}},
    {{"name": "人工智能", "type": "Concept", "importance": 0.9}}
]

只返回JSON列表，不要包含其他文字说明。
"""


def parse_entity_response(response: str) -> List[Dict[str, Any]]:
    """改进的JSON响应解析"""
    try:
        # 尝试直接解析
        result = json.loads(response)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'entities' in result:
            return result['entities']
        else:
            return []
    except:
        # 尝试提取JSON数组
        array_match = re.search(r'\[.*?\]', response, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group())
            except:
                pass
        
        # 尝试提取单个实体
        entities = []
        entity_pattern = r'\{"name":\s*"([^"]+)",\s*"type":\s*"([^"]+)",\s*"importance":\s*([\d.]+)\}'
        matches = re.finditer(entity_pattern, response)
        
        for match in matches:
            entities.append({
                "name": match.group(1),
                "type": match.group(2),
                "importance": float(match.group(3))
            })
        
        return entities


def create_relationship_extraction_prompt(text: str, entities: List[str]) -> str:
    """创建关系提取提示"""
    entity_list = ", ".join(entities[:10])  # 限制实体数量
    
    return f"""
在以下文本中识别这些实体之间的关系：

实体列表：{entity_list}

文本内容：
{text[:1000]}

请识别实体之间的关系，返回JSON格式的列表，每个关系包含：
- source: 源实体名称
- target: 目标实体名称  
- type: 关系类型（如：隶属于、合作、竞争、包含、相关等）
- description: 关系描述

例如：
[
    {{"source": "OpenAI", "target": "GPT-4", "type": "开发", "description": "OpenAI开发了GPT-4"}},
    {{"source": "GPT-4", "target": "人工智能", "type": "属于", "description": "GPT-4是人工智能技术"}}
]

只返回JSON列表。
"""


async def enhanced_extract_entities(chunks: List[Any], llm) -> List[Dict[str, Any]]:
    """增强的实体提取"""
    all_entities = []
    
    # 处理更多块，提高覆盖率
    for i, chunk in enumerate(chunks[:10]):  # 增加到10个块
        try:
            prompt = create_improved_entity_extraction_prompt(chunk.content)
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            
            chunk_entities = parse_entity_response(response.content)
            
            # 添加来源信息
            for entity in chunk_entities:
                entity['chunk_index'] = i
                entity['context'] = chunk.content[:200]
            
            all_entities.extend(chunk_entities)
            
        except Exception as e:
            print(f"Error extracting entities from chunk {i}: {e}")
            continue
    
    # 实体去重和合并
    unique_entities = {}
    for entity in all_entities:
        name = entity.get("name", "").strip()
        if not name:
            continue
            
        if name not in unique_entities:
            unique_entities[name] = entity
            unique_entities[name]['occurrences'] = 1
        else:
            # 合并信息
            unique_entities[name]['importance'] = max(
                unique_entities[name].get('importance', 0),
                entity.get('importance', 0)
            )
            unique_entities[name]['occurrences'] += 1
    
    # 根据出现次数和重要性排序
    entities = list(unique_entities.values())
    entities.sort(key=lambda x: (x['occurrences'], x.get('importance', 0)), reverse=True)
    
    return entities[:50]  # 返回前50个最重要的实体


async def enhanced_extract_relationships(chunks: List[Any], entities: List[Dict[str, Any]], llm) -> List[Dict[str, Any]]:
    """增强的关系提取"""
    relationships = []
    entity_names = [e['name'] for e in entities[:20]]  # 使用前20个实体
    
    # 使用更智能的关系提取
    for chunk in chunks[:5]:
        try:
            prompt = create_relationship_extraction_prompt(chunk.content, entity_names)
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            
            chunk_relationships = parse_entity_response(response.content)
            
            # 验证关系中的实体是否存在
            for rel in chunk_relationships:
                if (rel.get('source') in entity_names and 
                    rel.get('target') in entity_names):
                    relationships.append(rel)
                    
        except Exception as e:
            print(f"Error extracting relationships: {e}")
            continue
    
    # 关系去重
    unique_relationships = []
    seen = set()
    
    for rel in relationships:
        key = (rel['source'], rel['target'], rel.get('type', 'related'))
        if key not in seen:
            seen.add(key)
            unique_relationships.append(rel)
    
    return unique_relationships


# 添加保存到Neo4j的功能
async def save_knowledge_graph_to_neo4j(entities: List[Dict[str, Any]], 
                                       relationships: List[Dict[str, Any]],
                                       neo4j_manager,
                                       document_id: str):
    """将知识图谱保存到Neo4j"""
    try:
        # 创建文档节点
        await neo4j_manager.run_query(
            """
            MERGE (d:Document {id: $document_id})
            SET d.updated_at = datetime()
            """,
            {"document_id": document_id}
        )
        
        # 批量创建实体节点
        for entity in entities:
            await neo4j_manager.run_query(
                """
                MERGE (e:Entity {name: $name})
                SET e.type = $type,
                    e.importance = $importance,
                    e.updated_at = datetime()
                MERGE (d:Document {id: $document_id})
                MERGE (d)-[:CONTAINS_ENTITY]->(e)
                """,
                {
                    "name": entity['name'],
                    "type": entity.get('type', 'Unknown'),
                    "importance": entity.get('importance', 0.5),
                    "document_id": document_id
                }
            )
        
        # 批量创建关系
        for rel in relationships:
            await neo4j_manager.run_query(
                """
                MERGE (e1:Entity {name: $source})
                MERGE (e2:Entity {name: $target})
                MERGE (e1)-[r:RELATED {type: $rel_type}]->(e2)
                SET r.description = $description,
                    r.document_id = $document_id,
                    r.created_at = datetime()
                """,
                {
                    "source": rel['source'],
                    "target": rel['target'],
                    "rel_type": rel.get('type', 'RELATED'),
                    "description": rel.get('description', ''),
                    "document_id": document_id
                }
            )
        
        return True
        
    except Exception as e:
        print(f"Error saving to Neo4j: {e}")
        return False


if __name__ == "__main__":
    print("Knowledge Graph Fix Module")
    print("=========================")
    print("This module provides enhanced entity and relationship extraction")
    print("Use the functions in this module to improve knowledge graph generation")