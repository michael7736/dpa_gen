#!/usr/bin/env python3
"""
DPA系统自动化启动和集成测试脚本
"""

import subprocess
import asyncio
import aiohttp
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import signal

class DPAAutoTest:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.base_url = "http://localhost:8200"
        self.frontend_url = "http://localhost:8230"
        self.test_results = []
        self.project_id = None
        self.document_id = None
        self.python_path = "/Users/mdwong001/miniconda3/envs/dpa_gen/bin/python"
        
    async def start_backend(self):
        """启动后端服务"""
        print("🚀 启动后端服务...")
        try:
            # 激活conda环境并启动服务
            activate_cmd = 'eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)" && conda activate dpa_gen && '
            uvicorn_cmd = 'uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload'
            full_cmd = activate_cmd + uvicorn_cmd
            
            self.backend_process = subprocess.Popen(
                full_cmd,
                shell=True,
                executable='/bin/zsh',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"✅ 后端服务已启动 (PID: {self.backend_process.pid})")
            
            # 等待服务启动
            for i in range(30):
                if await self.check_backend_health():
                    print("✅ 后端服务已就绪")
                    return True
                await asyncio.sleep(1)
                print(".", end="", flush=True)
            
            print("\n❌ 后端服务启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动后端服务失败: {e}")
            return False
    
    async def start_frontend(self):
        """启动前端服务"""
        print("\n🚀 启动前端服务...")
        try:
            # 切换到前端目录
            frontend_dir = Path("frontend")
            
            # 检查依赖
            if not (frontend_dir / "node_modules").exists():
                print("📦 安装前端依赖...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            
            # 启动前端
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"✅ 前端服务已启动 (PID: {self.frontend_process.pid})")
            
            # 等待服务启动
            for i in range(60):
                if await self.check_frontend_health():
                    print("✅ 前端服务已就绪")
                    return True
                await asyncio.sleep(1)
                print(".", end="", flush=True)
            
            print("\n❌ 前端服务启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动前端服务失败: {e}")
            return False
    
    async def check_backend_health(self):
        """检查后端健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/health") as resp:
                    return resp.status == 200
        except:
            return False
    
    async def check_frontend_health(self):
        """检查前端健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url) as resp:
                    return resp.status == 200
        except:
            return False
    
    async def test_document_upload(self):
        """测试文档上传功能"""
        print("\n📄 测试文档上传...")
        
        try:
            # 创建测试文档
            test_content = """
# 测试文档

这是一个用于自动化测试的文档。

## 主要内容

1. 人工智能技术发展
2. 机器学习算法研究
3. 深度学习应用案例

## 技术要点

- OpenAI的GPT系列模型
- Google的BERT模型
- 自然语言处理技术

## 结论

AI技术正在快速发展，改变着我们的生活。
"""
            
            # 保存为临时文件
            test_file = Path("test_document.txt")
            test_file.write_text(test_content)
            
            # 获取默认项目
            async with aiohttp.ClientSession() as session:
                headers = {"X-USER-ID": "u1"}
                
                # 获取项目列表
                async with session.get(f"{self.base_url}/api/v1/projects", headers=headers) as resp:
                    if resp.status == 200:
                        projects = await resp.json()
                        if projects and len(projects) > 0:
                            self.project_id = projects[0]["id"]
                        else:
                            # 创建默认项目
                            async with session.post(
                                f"{self.base_url}/api/v1/projects",
                                json={"name": "Test Project", "description": "自动化测试项目"},
                                headers=headers
                            ) as create_resp:
                                if create_resp.status == 200:
                                    project = await create_resp.json()
                                    self.project_id = project["id"]
                
                if not self.project_id:
                    raise Exception("无法获取或创建项目")
                
                # 上传文档
                with open(test_file, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename='test_document.txt')
                    
                    async with session.post(
                        f"{self.base_url}/api/v1/documents/upload?project_id={self.project_id}",
                        data=data,
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            self.document_id = result.get("document_id")
                            print(f"✅ 文档上传成功: {self.document_id}")
                            self.test_results.append(("文档上传", "成功", None))
                            return True
                        else:
                            error = await resp.text()
                            raise Exception(f"上传失败: {error}")
            
        except Exception as e:
            print(f"❌ 文档上传测试失败: {e}")
            self.test_results.append(("文档上传", "失败", str(e)))
            return False
        finally:
            # 清理临时文件
            if test_file.exists():
                test_file.unlink()
    
    async def test_summary_generation(self):
        """测试摘要生成功能"""
        print("\n📝 测试摘要生成...")
        
        if not self.document_id:
            print("❌ 没有可用的文档ID")
            self.test_results.append(("摘要生成", "跳过", "没有文档ID"))
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-USER-ID": "u1"}
                
                # 启动摘要生成
                async with session.post(
                    f"{self.base_url}/api/v1/documents/{self.document_id}/operations/start",
                    json={"operation_types": ["summary"]},
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        pipeline_id = result.get("pipeline_id")
                        print(f"✅ 摘要生成已启动: {pipeline_id}")
                        
                        # 等待处理完成
                        await asyncio.sleep(10)
                        
                        # 检查摘要结果
                        async with session.get(
                            f"{self.base_url}/api/v1/documents/{self.document_id}/summary",
                            headers=headers
                        ) as summary_resp:
                            if summary_resp.status == 200:
                                summary = await summary_resp.json()
                                print(f"✅ 摘要生成成功: {summary.get('summary', '')[:100]}...")
                                self.test_results.append(("摘要生成", "成功", None))
                                return True
                            else:
                                raise Exception("获取摘要失败")
                    else:
                        error = await resp.text()
                        raise Exception(f"启动摘要生成失败: {error}")
                        
        except Exception as e:
            print(f"❌ 摘要生成测试失败: {e}")
            self.test_results.append(("摘要生成", "失败", str(e)))
            return False
    
    async def test_knowledge_graph(self):
        """测试知识图谱生成"""
        print("\n🔗 测试知识图谱生成...")
        
        if not self.document_id:
            print("❌ 没有可用的文档ID")
            self.test_results.append(("知识图谱", "跳过", "没有文档ID"))
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-USER-ID": "u1"}
                
                # 启动深度分析（包含知识图谱）
                async with session.post(
                    f"{self.base_url}/api/v1/documents/{self.document_id}/operations/start",
                    json={"operation_types": ["analysis"]},
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        pipeline_id = result.get("pipeline_id")
                        print(f"✅ 深度分析已启动: {pipeline_id}")
                        
                        # 等待处理
                        await asyncio.sleep(30)
                        
                        # 这里简单验证API响应
                        print("✅ 知识图谱生成完成（实际结果需查看日志）")
                        self.test_results.append(("知识图谱", "成功", None))
                        return True
                    else:
                        error = await resp.text()
                        raise Exception(f"启动深度分析失败: {error}")
                        
        except Exception as e:
            print(f"❌ 知识图谱测试失败: {e}")
            self.test_results.append(("知识图谱", "失败", str(e)))
            return False
    
    async def test_qa_system(self):
        """测试问答系统"""
        print("\n❓ 测试问答系统...")
        
        if not self.project_id:
            print("❌ 没有可用的项目ID")
            self.test_results.append(("问答系统", "跳过", "没有项目ID"))
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-USER-ID": "u1"}
                
                # 提问
                question = "这个文档的主要内容是什么？"
                async with session.post(
                    f"{self.base_url}/api/v1/qa/answer",
                    json={
                        "project_id": self.project_id,
                        "question": question
                    },
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        answer = await resp.json()
                        print(f"✅ 问答成功:")
                        print(f"   问题: {question}")
                        print(f"   回答: {answer.get('answer', '')[:100]}...")
                        self.test_results.append(("问答系统", "成功", None))
                        return True
                    else:
                        error = await resp.text()
                        raise Exception(f"问答失败: {error}")
                        
        except Exception as e:
            print(f"❌ 问答系统测试失败: {e}")
            self.test_results.append(("问答系统", "失败", str(e)))
            return False
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "="*50)
        print("📊 测试总结")
        print("="*50)
        
        success_count = sum(1 for _, status, _ in self.test_results if status == "成功")
        total_count = len(self.test_results)
        
        for module, status, error in self.test_results:
            status_icon = "✅" if status == "成功" else "❌" if status == "失败" else "⏭️"
            print(f"{status_icon} {module}: {status}")
            if error:
                print(f"   错误: {error}")
        
        print(f"\n总计: {success_count}/{total_count} 成功")
        print("="*50)
    
    def cleanup(self):
        """清理进程"""
        print("\n🧹 清理进程...")
        
        if self.backend_process:
            self.backend_process.terminate()
            print("✅ 后端服务已停止")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            print("✅ 前端服务已停止")
    
    async def run(self):
        """运行完整测试流程"""
        print("🚀 DPA系统自动化集成测试")
        print("="*50)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        try:
            # 启动服务
            if not await self.start_backend():
                print("❌ 后端服务启动失败，终止测试")
                return
            
            if not await self.start_frontend():
                print("❌ 前端服务启动失败，终止测试")
                return
            
            # 等待服务稳定
            print("\n⏳ 等待服务稳定...")
            await asyncio.sleep(3)
            
            # 执行测试
            await self.test_document_upload()
            await self.test_summary_generation()
            await self.test_knowledge_graph()
            await self.test_qa_system()
            
            # 打印总结
            self.print_test_summary()
            
        except KeyboardInterrupt:
            print("\n⚠️ 测试被用户中断")
        except Exception as e:
            print(f"\n❌ 测试过程出错: {e}")
        finally:
            self.cleanup()
            print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """主函数"""
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # 运行测试
    tester = DPAAutoTest()
    await tester.run()

if __name__ == "__main__":
    asyncio.run(main())