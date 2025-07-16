#!/usr/bin/env python3
"""
简单的Neo4j设置脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/mdwong001/Desktop/code/rag/DPA')

def setup_neo4j():
    """设置Neo4j数据库"""
    print("🔧 设置Neo4j数据库")
    print("=" * 50)
    
    try:
        # 导入Neo4j驱动
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv()
        
        # 获取连接信息
        neo4j_url = os.getenv("NEO4J_URL", "bolt://rtx4080:7687")
        neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "1234qwer")
        
        print(f"连接信息:")
        print(f"  URL: {neo4j_url}")
        print(f"  用户: {neo4j_user}")
        
        # 连接到Neo4j
        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))
        
        print(f"\n✅ Neo4j连接成功")
        
        # 测试连接
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            print(f"连接测试: {result.single()}")
        
        # 尝试创建dpa_graph数据库
        print(f"\n🔄 尝试创建dpa_graph数据库...")
        try:
            with driver.session() as session:
                session.run("CREATE DATABASE dpa_graph IF NOT EXISTS")
                print("✅ dpa_graph数据库创建成功")
        except Exception as e:
            print(f"⚠️  创建数据库失败（可能已存在）: {e}")
            print("将使用默认数据库")
        
        # 创建基本索引
        print(f"\n📊 创建基本索引...")
        try:
            # 尝试连接到dpa_graph数据库
            with driver.session(database="dpa_graph") as session:
                indexes = [
                    "CREATE INDEX document_id_idx IF NOT EXISTS FOR (d:Document) ON (d.id)",
                    "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                    "CREATE INDEX chunk_id_idx IF NOT EXISTS FOR (c:Chunk) ON (c.id)"
                ]
                
                for idx in indexes:
                    try:
                        session.run(idx)
                        print(f"✅ {idx.split()[2]} 创建成功")
                    except Exception as e:
                        print(f"⚠️  索引创建失败: {e}")
        except Exception as e:
            print(f"⚠️  连接dpa_graph失败，尝试默认数据库: {e}")
            # 使用默认数据库
            with driver.session() as session:
                indexes = [
                    "CREATE INDEX document_id_idx IF NOT EXISTS FOR (d:Document) ON (d.id)",
                    "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                    "CREATE INDEX chunk_id_idx IF NOT EXISTS FOR (c:Chunk) ON (c.id)"
                ]
                
                for idx in indexes:
                    try:
                        session.run(idx)
                        print(f"✅ {idx.split()[2]} 创建成功（默认数据库）")
                    except Exception as e:
                        print(f"⚠️  索引创建失败: {e}")
        
        driver.close()
        print(f"\n✅ Neo4j配置完成")
        return True
        
    except ImportError as e:
        print(f"❌ Neo4j驱动未安装: {e}")
        return False
    except Exception as e:
        print(f"❌ Neo4j配置失败: {e}")
        return False

if __name__ == "__main__":
    success = setup_neo4j()
    if success:
        print("\n🎉 Neo4j设置成功！")
    else:
        print("\n💥 Neo4j设置失败！")
        sys.exit(1)