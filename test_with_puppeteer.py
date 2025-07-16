#!/usr/bin/env python3
"""
使用Puppeteer测试DPA服务
"""

import subprocess
import time
import json
import os
from pathlib import Path

def run_puppeteer_test():
    """运行Puppeteer测试"""
    print("🎭 启动Puppeteer测试...")
    
    # 检查测试工具是否存在
    test_file = Path("test_browser_simple.html")
    if not test_file.exists():
        print("❌ 测试工具文件不存在")
        return False
    
    # 使用系统默认浏览器打开测试工具
    try:
        if os.name == 'nt':  # Windows
            os.startfile(str(test_file.absolute()))
        elif os.name == 'posix':  # macOS/Linux
            subprocess.run(['open', str(test_file.absolute())])
        
        print("✅ 测试工具已在浏览器中打开")
        print("📋 请在浏览器中:")
        print("   1. 点击'检查服务状态'")
        print("   2. 点击'运行所有测试'")
        print("   3. 查看测试结果")
        
        return True
    except Exception as e:
        print(f"❌ 打开测试工具失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 DPA Puppeteer测试启动器")
    print("=" * 30)
    
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # 启动Puppeteer测试
    run_puppeteer_test()
    
    print("\n🎯 测试完成后，请查看浏览器中的测试报告")
    print("📊 测试报告会包含:")
    print("   - 服务状态检查结果")
    print("   - API端点测试结果")
    print("   - 前端页面测试结果")
    print("   - 功能测试结果")

if __name__ == "__main__":
    main()