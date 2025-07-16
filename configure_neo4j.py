#!/usr/bin/env python3
"""
配置Neo4j数据库
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def configure_neo4j():
    """配置Neo4j数据库"""
    print("🔧 配置Neo4j数据库")
    print("=" * 50)
    
    # 获取Neo4j连接信息
    neo4j_url = os.getenv("NEO4J_URL", "bolt://rtx4080:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "1234qwer")
    
    print(f"Neo4j URL: {neo4j_url}")
    print(f"Neo4j User: {neo4j_user}")
    
    try:
        # 连接到Neo4j
        print("\n1️⃣ 连接到Neo4j...")
        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))
        
        # 检查连接
        print("2️⃣ 测试连接...")
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_result = result.single()
            print(f"   ✅ 连接成功: {test_result}")
        
        # 检查是否存在dpa_graph数据库
        print("\n3️⃣ 检查数据库...")
        try:
            with driver.session() as session:
                databases = session.run("SHOW DATABASES").data()
                print("   现有数据库:")
                for db in databases:
                    print(f"   - {db['name']}: {db['currentStatus']}")
                    
                # 检查dpa_graph是否存在
                dpa_graph_exists = any(db['name'] == 'dpa_graph' for db in databases)
                
                if not dpa_graph_exists:
                    print("\n4️⃣ 创建dpa_graph数据库...")
                    try:
                        session.run("CREATE DATABASE dpa_graph")
                        print("   ✅ dpa_graph数据库创建成功")
                    except Exception as e:
                        print(f"   ❌ 创建数据库失败: {e}")
                        print("   将使用默认数据库neo4j")
                else:
                    print("   ✅ dpa_graph数据库已存在")
                    
        except Exception as e:
            print(f"   ⚠️  无法列出数据库（可能是权限问题）: {e}")
            print("   将使用默认数据库")
        
        # 连接到dpa_graph数据库
        print("\n5️⃣ 连接到dpa_graph数据库...")
        try:
            with driver.session(database="dpa_graph") as session:
                # 创建基本索引
                print("6️⃣ 创建基本索引...")
                index_queries = [
                    "CREATE INDEX document_id_index IF NOT EXISTS FOR (d:Document) ON (d.id)",
                    "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                    "CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name)",
                    "CREATE INDEX chunk_id_index IF NOT EXISTS FOR (ch:Chunk) ON (ch.id)",
                ]
                
                for query in index_queries:
                    try:
                        session.run(query)
                        index_name = query.split(' ')[2]
                        print(f"   ✅ 索引创建成功: {index_name}")
                    except Exception as e:
                        print(f"   ⚠️  索引创建失败: {e}")
                
                # 验证索引
                print("\n7️⃣ 验证索引...")
                try:
                    indexes = session.run("SHOW INDEXES").data()
                    print("   已创建的索引:")
                    for idx in indexes:
                        print(f"   - {idx.get('name', 'unnamed')}: {idx.get('state', 'unknown')}")
                except Exception as e:
                    print(f"   ⚠️  无法列出索引: {e}")
                
                print("\n✅ Neo4j配置完成!")
                return True
                
        except Exception as e:
            print(f"   ❌ 连接dpa_graph失败: {e}")
            print("   尝试使用默认数据库...")
            
            # 回退到默认数据库
            try:
                with driver.session() as session:
                    session.run("RETURN 1")
                    print("   ✅ 使用默认数据库成功")
                    return True
            except Exception as e2:
                print(f"   ❌ 连接默认数据库也失败: {e2}")
                return False
        
        finally:
            driver.close()
                
    except Exception as e:
        print(f"❌ Neo4j配置失败: {e}")
        return False

def main():
    """主函数"""
    success = configure_neo4j()
    
    if success:
        print("\n🎉 Neo4j配置成功!")
        print("现在可以重启API服务以应用更改。")
    else:
        print("\n💥 Neo4j配置失败!")
        print("请检查Neo4j服务状态和连接配置。")
        sys.exit(1)

if __name__ == "__main__":
    main()