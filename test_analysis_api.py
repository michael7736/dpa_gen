#!/usr/bin/env python3
"""
测试高级文档分析API
"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_api_health():
    """测试API健康状态"""
    print("=== 测试API健康状态 ===")
    try:
        response = requests.get(f"http://localhost:8001/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False


def test_quick_analysis():
    """测试快速文本分析功能"""
    print("\n=== 测试快速文本分析 ===")
    
    test_text = """
    人工智能（AI）正在彻底改变教育领域。通过个性化学习系统，AI能够根据每个学生的学习速度和风格定制教育内容。
    研究表明，使用AI辅助学习的学生平均成绩提高了30%。然而，这也带来了新的挑战，如数据隐私和教师角色的转变。
    未来，混合式学习模式将成为主流，结合AI的优势和人类教师的创造力与同理心。
    """
    
    payload = {
        "content": test_text,
        "title": "AI教育应用测试",
        "analysis_depth": "basic",
        "analysis_goal": "理解AI在教育中的应用和影响"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analysis/analyze-text?user_id=test_user",
            json=payload
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n分析结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")


def test_templates():
    """测试获取分析模板"""
    print("\n=== 测试获取分析模板 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/analysis/templates")
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n可用模板:")
            for template in result["templates"]:
                print(f"- {template['name']} ({template['id']}): {template['description']}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")


def test_list_analyses():
    """测试列出分析任务"""
    print("\n=== 测试列出分析任务 ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/analysis/list?user_id=test_user&page=1&per_page=10"
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n找到 {result['total']} 个分析任务")
            for analysis in result.get("analyses", []):
                print(f"- {analysis['analysis_id']}: {analysis['status']} ({analysis['progress']}%)")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")


if __name__ == "__main__":
    print("开始测试高级文档分析API...")
    print(f"API地址: {BASE_URL}\n")
    
    # 测试API健康状态
    if test_api_health():
        print("\n✅ API服务正常运行")
        
        # 测试获取模板
        test_templates()
        
        # 测试快速分析
        test_quick_analysis()
        
        # 测试列出分析
        test_list_analyses()
    else:
        print("\n❌ API服务未运行或无法访问")
    
    print("\n测试完成！")