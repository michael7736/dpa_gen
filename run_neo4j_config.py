#!/usr/bin/env python3
"""
运行Neo4j配置的简单脚本
"""
import sys
import os
sys.path.insert(0, '/Users/mdwong001/mambaforge/envs/dpa_gen/lib/python3.11/site-packages')

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/mdwong001/Desktop/code/rag/DPA'

# 执行配置
exec(open('/Users/mdwong001/Desktop/code/rag/DPA/configure_neo4j.py').read())