#!/usr/bin/env python3
"""
Memory Bank命令行管理工具
"""
import asyncio
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def list_projects(args):
    """列出所有项目"""
    manager = create_memory_bank_manager(user_id=args.user)
    
    base_path = Path(manager.base_path)
    if args.user != "u1":
        base_path = base_path / args.user
        
    if not base_path.exists():
        print(f"No projects found for user: {args.user}")
        return
        
    projects = []
    for project_dir in base_path.glob("project_*"):
        if project_dir.is_dir():
            project_id = project_dir.name.replace("project_", "")
            
            # 读取元数据
            metadata_file = project_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                projects.append([
                    project_id,
                    metadata.get("created_at", "")[:19],
                    metadata.get("updated_at", "")[:19],
                    metadata.get("stats", {}).get("total_interactions", 0),
                    metadata.get("stats", {}).get("total_concepts", 0)
                ])
                
    if projects:
        headers = ["Project ID", "Created", "Updated", "Interactions", "Concepts"]
        print(f"\nProjects for user: {args.user}")
        print(tabulate(projects, headers=headers, tablefmt="grid"))
    else:
        print(f"No projects found for user: {args.user}")


async def show_project(args):
    """显示项目详情"""
    manager = create_memory_bank_manager(user_id=args.user)
    snapshot = await manager.get_snapshot(args.project_id)
    
    if not snapshot:
        print(f"Project {args.project_id} not found")
        return
        
    print(f"\n=== Project: {args.project_id} ===")
    print(f"User: {snapshot['user_id']}")
    print(f"Last Updated: {snapshot['last_updated']}")
    print(f"Concepts Count: {snapshot['concepts_count']}")
    
    # 显示概念
    if snapshot['top_concepts']:
        print("\nTop Concepts:")
        for i, concept in enumerate(snapshot['top_concepts'][:10], 1):
            print(f"  {i}. {concept['name']} ({concept['category']}) - Frequency: {concept['frequency']}")
            
    # 显示上下文预览
    print(f"\nContext Preview:")
    print("-" * 60)
    print(snapshot['context_preview'])
    print("-" * 60)
    
    # 显示最近活动
    if snapshot.get('recent_activities'):
        print("\nRecent Activities:")
        for activity in snapshot['recent_activities'][:5]:
            print(f"  - [{activity['timestamp'][:19]}] {activity['event_type']}: {activity['content']}")


async def init_project(args):
    """初始化项目"""
    manager = create_memory_bank_manager(user_id=args.user)
    success = await manager.initialize_project(args.project_id)
    
    if success:
        print(f"✓ Project {args.project_id} initialized successfully")
    else:
        print(f"✗ Failed to initialize project {args.project_id}")


async def update_context(args):
    """更新项目上下文"""
    manager = create_memory_bank_manager(user_id=args.user)
    
    # 从文件或标准输入读取内容
    if args.file:
        with open(args.file, 'r') as f:
            content = f.read()
    else:
        print("Enter context (Ctrl+D to finish):")
        content = sys.stdin.read()
        
    success = await manager.update_context(
        project_id=args.project_id,
        new_content=content,
        source=args.source or "cli"
    )
    
    if success:
        print(f"✓ Context updated successfully ({len(content)} characters)")
    else:
        print(f"✗ Failed to update context")


async def add_concept(args):
    """添加概念"""
    manager = create_memory_bank_manager(user_id=args.user)
    
    concept = {
        "name": args.name,
        "category": args.category or "general",
        "description": args.description or ""
    }
    
    if args.relationships:
        concept["relationships"] = args.relationships.split(",")
        
    added = await manager.add_concepts(args.project_id, [concept])
    
    if added > 0:
        print(f"✓ Concept '{args.name}' added successfully")
    else:
        print(f"✓ Concept '{args.name}' updated (already exists)")


async def search_concepts(args):
    """搜索概念"""
    manager = create_memory_bank_manager(user_id=args.user)
    results = await manager.search_concepts(
        project_id=args.project_id,
        query=args.query,
        category=args.category
    )
    
    if results:
        print(f"\nFound {len(results)} concepts:")
        for concept in results:
            print(f"\n- {concept['name']} ({concept['category']})")
            print(f"  Description: {concept['description']}")
            print(f"  Frequency: {concept['frequency']}")
            if concept.get('relationships'):
                print(f"  Related to: {', '.join(concept['relationships'])}")
    else:
        print(f"No concepts found matching '{args.query}'")


async def update_summary(args):
    """更新项目摘要"""
    manager = create_memory_bank_manager(user_id=args.user)
    
    print("Generating summary...")
    summary = await manager.update_summary(
        project_id=args.project_id,
        force_regenerate=True
    )
    
    print("\n=== Updated Summary ===")
    print(summary)


async def export_project(args):
    """导出项目"""
    manager = create_memory_bank_manager(user_id=args.user)
    export_data = await manager.export_memory(args.project_id)
    
    if not export_data:
        print(f"Project {args.project_id} not found")
        return
        
    # 保存到文件
    output_file = args.output or f"{args.project_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
        
    print(f"✓ Project exported to: {output_file}")
    print(f"  Total concepts: {export_data['statistics']['total_concepts']}")
    print(f"  Journal entries: {export_data['statistics']['journal_entries']}")


def main():
    parser = argparse.ArgumentParser(description="Memory Bank CLI Tool")
    parser.add_argument("--user", "-u", default="u1", help="User ID (default: u1)")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List projects
    list_parser = subparsers.add_parser("list", help="List all projects")
    
    # Show project
    show_parser = subparsers.add_parser("show", help="Show project details")
    show_parser.add_argument("project_id", help="Project ID")
    
    # Initialize project
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("project_id", help="Project ID")
    
    # Update context
    context_parser = subparsers.add_parser("context", help="Update project context")
    context_parser.add_argument("project_id", help="Project ID")
    context_parser.add_argument("--file", "-f", help="Read content from file")
    context_parser.add_argument("--source", "-s", help="Content source")
    
    # Add concept
    concept_parser = subparsers.add_parser("concept", help="Add a concept")
    concept_parser.add_argument("project_id", help="Project ID")
    concept_parser.add_argument("name", help="Concept name")
    concept_parser.add_argument("--category", "-c", help="Concept category")
    concept_parser.add_argument("--description", "-d", help="Concept description")
    concept_parser.add_argument("--relationships", "-r", help="Related concepts (comma-separated)")
    
    # Search concepts
    search_parser = subparsers.add_parser("search", help="Search concepts")
    search_parser.add_argument("project_id", help="Project ID")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--category", "-c", help="Filter by category")
    
    # Update summary
    summary_parser = subparsers.add_parser("summary", help="Update project summary")
    summary_parser.add_argument("project_id", help="Project ID")
    
    # Export project
    export_parser = subparsers.add_parser("export", help="Export project")
    export_parser.add_argument("project_id", help="Project ID")
    export_parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # 执行命令
    commands = {
        "list": list_projects,
        "show": show_project,
        "init": init_project,
        "context": update_context,
        "concept": add_concept,
        "search": search_concepts,
        "summary": update_summary,
        "export": export_project
    }
    
    if args.command in commands:
        asyncio.run(commands[args.command](args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()