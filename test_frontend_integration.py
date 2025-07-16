#!/usr/bin/env python3
"""
前端集成测试脚本
验证AAG页面的完整功能
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_frontend_build():
    """检查前端构建状态"""
    print("🔍 检查前端构建状态...")
    
    frontend_dir = Path("/Users/mdwong001/Desktop/code/rag/DPA/frontend")
    if not frontend_dir.exists():
        print("❌ 前端目录不存在")
        return False
    
    # 检查package.json
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json不存在")
        return False
    
    # 检查node_modules
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("⚠️  node_modules不存在，需要运行npm install")
        return False
    
    print("✅ 前端基础文件检查通过")
    return True

def check_component_files():
    """检查关键组件文件"""
    print("\n🔍 检查关键组件文件...")
    
    components_to_check = [
        "frontend/src/app/aag/page.tsx",
        "frontend/src/components/aag/ResultViewModal.tsx",
        "frontend/src/components/aag/DocumentActions.tsx",
        "frontend/src/components/aag/EnhancedDocumentViewer.tsx",
        "frontend/src/services/documentResults.ts",
        "frontend/src/services/documentsV2.ts"
    ]
    
    missing_files = []
    for component in components_to_check:
        file_path = Path(component)
        if not file_path.exists():
            missing_files.append(component)
        else:
            print(f"✅ {component}")
    
    if missing_files:
        print(f"❌ 缺失文件: {missing_files}")
        return False
    
    print("✅ 所有关键组件文件存在")
    return True

def check_imports_and_exports():
    """检查导入导出"""
    print("\n🔍 检查导入导出...")
    
    # 检查AAG页面是否正确导入ResultViewModal
    aag_page = Path("frontend/src/app/aag/page.tsx")
    if aag_page.exists():
        content = aag_page.read_text()
        if "import ResultViewModal" in content:
            print("✅ AAG页面正确导入ResultViewModal")
        else:
            print("❌ AAG页面未导入ResultViewModal")
            return False
            
        if "onViewResult={handleViewResult}" in content:
            print("✅ AAG页面正确传递onViewResult属性")
        else:
            print("❌ AAG页面未传递onViewResult属性")
            return False
            
        if "<ResultViewModal" in content:
            print("✅ AAG页面正确使用ResultViewModal组件")
        else:
            print("❌ AAG页面未使用ResultViewModal组件")
            return False
    
    # 检查EnhancedDocumentViewer是否支持onViewResult
    viewer_component = Path("frontend/src/components/aag/EnhancedDocumentViewer.tsx")
    if viewer_component.exists():
        content = viewer_component.read_text()
        if "onViewResult?" in content:
            print("✅ EnhancedDocumentViewer支持onViewResult属性")
        else:
            print("❌ EnhancedDocumentViewer不支持onViewResult属性")
            return False
    
    print("✅ 导入导出检查通过")
    return True

def check_typescript_compilation():
    """检查TypeScript编译"""
    print("\n🔍 检查TypeScript编译...")
    
    try:
        os.chdir("frontend")
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--skipLibCheck"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ TypeScript编译检查通过")
            return True
        else:
            print(f"❌ TypeScript编译错误:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ TypeScript编译检查失败: {e}")
        return False
    finally:
        os.chdir("..")

def check_api_endpoints():
    """检查API端点"""
    print("\n🔍 检查API端点...")
    
    # 检查documentResults服务
    service_file = Path("frontend/src/services/documentResults.ts")
    if service_file.exists():
        content = service_file.read_text()
        expected_endpoints = [
            "/api/v1/documents/${documentId}/summary",
            "/api/v1/documents/${documentId}/analysis",
            "/api/v1/documents/${documentId}/operations/status"
        ]
        
        all_endpoints_found = True
        for endpoint in expected_endpoints:
            if endpoint in content:
                print(f"✅ API端点存在: {endpoint}")
            else:
                print(f"❌ API端点缺失: {endpoint}")
                all_endpoints_found = False
        
        if all_endpoints_found:
            print("✅ 所有API端点检查通过")
            return True
        else:
            print("❌ 部分API端点缺失")
            return False
    
    print("❌ documentResults服务文件不存在")
    return False

def generate_integration_report():
    """生成集成报告"""
    print("\n" + "="*60)
    print("📊 前端集成测试报告")
    print("="*60)
    
    tests = [
        ("前端构建检查", check_frontend_build),
        ("组件文件检查", check_component_files),
        ("导入导出检查", check_imports_and_exports),
        ("TypeScript编译检查", check_typescript_compilation),
        ("API端点检查", check_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 统计结果
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📊 测试结果统计:")
    print(f"通过测试: {passed_tests}/{total_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 前端集成状态良好")
    elif success_rate >= 60:
        print("⚠️  前端集成需要优化")
    else:
        print("❌ 前端集成存在严重问题")
    
    # 生成详细报告
    print(f"\n📝 详细结果:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    return success_rate >= 80

def main():
    """主函数"""
    print("🚀 启动前端集成测试")
    print("="*60)
    
    # 切换到项目根目录
    os.chdir("/Users/mdwong001/Desktop/code/rag/DPA")
    
    # 运行测试
    success = generate_integration_report()
    
    if success:
        print("\n🎯 建议的下一步操作:")
        print("1. 启动前端开发服务器: cd frontend && npm run dev")
        print("2. 启动后端API服务器: uvicorn src.api.main:app --reload --port 8200")
        print("3. 访问AAG页面: http://localhost:8230/aag")
        print("4. 测试文档上传和结果查看功能")
    else:
        print("\n🔧 需要修复的问题:")
        print("1. 检查组件导入导出是否正确")
        print("2. 确认TypeScript类型定义")
        print("3. 验证API端点配置")
        print("4. 测试组件集成")

if __name__ == "__main__":
    main()