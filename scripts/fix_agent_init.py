#!/usr/bin/env python3
"""
修复所有Agent的__init__方法，添加缺少的name参数
"""

import re
import os
from pathlib import Path

# 需要修复的文件列表
files_to_fix = [
    "src/aag/agents/planner.py",
    "src/aag/agents/skimmer.py",
    "src/aag/agents/summarizer.py",
    "src/aag/agents/knowledge_graph.py",
    "src/aag/agents/outliner.py",
]

# 修复映射
class_name_mapping = {
    "PlannerAgent": "PlannerAgent",
    "SkimmerAgent": "SkimmerAgent",
    "ProgressiveSummaryAgent": "ProgressiveSummaryAgent",
    "KnowledgeGraphAgent": "KnowledgeGraphAgent",
    "OutlineAgent": "OutlineAgent",
}


def fix_super_init(file_path):
    """修复文件中的super().__init__调用"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找类定义
    class_pattern = r'class\s+(\w+)\(BaseAgent\):'
    class_matches = re.findall(class_pattern, content)
    
    if not class_matches:
        print(f"未在 {file_path} 中找到继承自BaseAgent的类")
        return False
    
    modified = False
    for class_name in class_matches:
        # 查找该类的__init__方法中的super().__init__调用
        init_pattern = rf'(class\s+{class_name}\(BaseAgent\):.*?def\s+__init__.*?)(super\(\).__init__\()([^)]+)\)'
        
        def replacer(match):
            prefix = match.group(1)
            super_call = match.group(2)
            params = match.group(3)
            
            # 检查参数是否已经包含name参数
            if 'name=' in params:
                return match.group(0)
            
            # 解析参数
            param_parts = [p.strip() for p in params.split(',')]
            
            # 构建新的super().__init__调用
            new_params = [f'name="{class_name}"']
            
            for param in param_parts:
                if param and '=' not in param:
                    # 位置参数，需要转换为关键字参数
                    if 'model' in param.lower() or param == param_parts[0]:
                        new_params.append(f'model_name={param}')
                    elif 'temp' in param.lower() or param == param_parts[1]:
                        new_params.append(f'temperature={param}')
                else:
                    new_params.append(param)
            
            new_call = prefix + super_call + ', '.join(new_params) + ')'
            return new_call
        
        new_content, count = re.subn(init_pattern, replacer, content, flags=re.DOTALL)
        
        if count > 0:
            content = new_content
            modified = True
            print(f"✅ 修复了 {file_path} 中的 {class_name}")
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return modified


def main():
    """主函数"""
    print("开始修复Agent初始化问题...")
    
    project_root = Path(__file__).parent.parent
    
    fixed_count = 0
    for file_path in files_to_fix:
        full_path = project_root / file_path
        
        if not full_path.exists():
            print(f"❌ 文件不存在: {full_path}")
            continue
        
        if fix_super_init(full_path):
            fixed_count += 1
    
    print(f"\n✅ 总共修复了 {fixed_count} 个文件")


if __name__ == "__main__":
    main()