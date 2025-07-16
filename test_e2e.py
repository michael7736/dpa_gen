#!/usr/bin/env python3
"""
端到端测试脚本
测试DPA系统的主要功能流程
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8001/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "X-USER-ID": "u1"
}

def print_result(test_name: str, success: bool, message: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"   {message}")

def test_health_check():
    """测试健康检查"""
    try:
        resp = requests.get(f"{BASE_URL}/health", headers=HEADERS)
        success = resp.status_code == 200
        print_result("Health Check", success, f"Status: {resp.status_code}")
        return success
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_get_projects():
    """测试获取项目列表"""
    try:
        resp = requests.get(f"{BASE_URL}/projects", headers=HEADERS)
        success = resp.status_code == 200
        data = resp.json()
        print_result("Get Projects", success, f"Found {data.get('total', 0)} projects")
        return success, data
    except Exception as e:
        print_result("Get Projects", False, str(e))
        return False, {}

def test_get_project_detail(project_id: str):
    """测试获取项目详情"""
    try:
        resp = requests.get(f"{BASE_URL}/projects/{project_id}", headers=HEADERS)
        success = resp.status_code == 200
        if success:
            data = resp.json()
            print_result("Get Project Detail", success, f"Project: {data.get('name', 'Unknown')}")
        else:
            print_result("Get Project Detail", success, f"Status: {resp.status_code}, Response: {resp.text}")
        return success
    except Exception as e:
        print_result("Get Project Detail", False, str(e))
        return False

def test_create_project():
    """测试创建项目"""
    try:
        project_data = {
            "name": f"测试项目_{int(time.time())}",
            "description": "端到端测试创建的项目"
        }
        resp = requests.post(f"{BASE_URL}/projects", headers=HEADERS, json=project_data)
        success = resp.status_code == 200
        if success:
            data = resp.json()
            print_result("Create Project", success, f"Created: {data.get('name')} (ID: {data.get('id')})")
            return success, data.get('id')
        else:
            print_result("Create Project", success, f"Status: {resp.status_code}, Response: {resp.text}")
            return success, None
    except Exception as e:
        print_result("Create Project", False, str(e))
        return False, None

def test_get_documents(project_id: str):
    """测试获取文档列表"""
    try:
        resp = requests.get(f"{BASE_URL}/documents", headers=HEADERS, params={"project_id": project_id})
        success = resp.status_code == 200
        data = resp.json()
        print_result("Get Documents", success, f"Found {data.get('total', 0)} documents")
        return success
    except Exception as e:
        print_result("Get Documents", False, str(e))
        return False

def test_get_conversations(project_id: str):
    """测试获取对话列表"""
    try:
        resp = requests.get(f"{BASE_URL}/conversations", headers=HEADERS, params={"project_id": project_id})
        success = resp.status_code == 200
        if success:
            data = resp.json()
            print_result("Get Conversations", success, f"Found {data.get('total', 0)} conversations")
        else:
            print_result("Get Conversations", success, f"Status: {resp.status_code}, Response: {resp.text}")
        return success
    except Exception as e:
        print_result("Get Conversations", False, str(e))
        return False

def main():
    """主测试流程"""
    print("🚀 开始端到端测试...\n")
    
    # 1. 健康检查
    if not test_health_check():
        print("\n❌ 健康检查失败，请确保后端服务正在运行")
        sys.exit(1)
    
    print()
    
    # 2. 获取项目列表
    success, projects_data = test_get_projects()
    if not success:
        print("\n❌ 无法获取项目列表")
        sys.exit(1)
    
    # 3. 如果有项目，测试获取项目详情
    if projects_data.get('items'):
        first_project = projects_data['items'][0]
        project_id = first_project['id']
        print(f"\n使用现有项目进行测试: {first_project['name']} (ID: {project_id})")
        
        test_get_project_detail(project_id)
        test_get_documents(project_id)
        test_get_conversations(project_id)
    else:
        print("\n没有找到现有项目，创建新项目...")
        success, project_id = test_create_project()
        if success and project_id:
            test_get_project_detail(project_id)
            test_get_documents(project_id)
            test_get_conversations(project_id)
    
    print("\n✅ 端到端测试完成！")

if __name__ == "__main__":
    main()