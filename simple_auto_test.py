#!/usr/bin/env python3
"""
简化的DPA自动启动和测试脚本
"""

import subprocess
import time
import requests
import json
from pathlib import Path

class SimpleDPATest:
    def __init__(self):
        self.backend_pid = None
        self.frontend_pid = None
        
    def start_backend(self):
        """启动后端服务"""
        print("🚀 启动后端服务...")
        
        # 创建启动脚本
        start_script = """#!/bin/zsh
cd /Users/mdwong001/Desktop/code/rag/DPA
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)"
conda activate dpa_gen
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload
"""
        
        # 保存脚本
        script_path = Path("start_backend_temp.sh")
        script_path.write_text(start_script)
        script_path.chmod(0o755)
        
        # 启动
        process = subprocess.Popen(["/bin/zsh", str(script_path)])
        self.backend_pid = process.pid
        print(f"✅ 后端服务已启动 (PID: {self.backend_pid})")
        
        # 等待启动
        print("⏳ 等待后端服务启动...", end="")
        for i in range(30):
            try:
                resp = requests.get("http://localhost:8200/api/v1/health", timeout=1)
                if resp.status_code == 200:
                    print("\n✅ 后端服务已就绪")
                    return True
            except:
                pass
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ 后端服务启动超时")
        return False
    
    def start_frontend(self):
        """启动前端服务"""
        print("\n🚀 启动前端服务...")
        
        # 创建启动脚本
        start_script = """#!/bin/zsh
cd /Users/mdwong001/Desktop/code/rag/DPA/frontend
npm run dev
"""
        
        # 保存脚本
        script_path = Path("start_frontend_temp.sh")
        script_path.write_text(start_script)
        script_path.chmod(0o755)
        
        # 启动
        process = subprocess.Popen(["/bin/zsh", str(script_path)])
        self.frontend_pid = process.pid
        print(f"✅ 前端服务已启动 (PID: {self.frontend_pid})")
        
        # 等待启动
        print("⏳ 等待前端服务启动...", end="")
        for i in range(60):
            try:
                resp = requests.get("http://localhost:8230", timeout=1)
                if resp.status_code == 200:
                    print("\n✅ 前端服务已就绪")
                    return True
            except:
                pass
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ 前端服务启动超时")
        return False
    
    def test_health_check(self):
        """测试健康检查"""
        print("\n🏥 测试健康检查...")
        try:
            resp = requests.get("http://localhost:8200/api/v1/health", 
                               headers={"X-USER-ID": "u1"})
            if resp.status_code == 200:
                print("✅ 健康检查通过")
                return True
            else:
                print(f"❌ 健康检查失败: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_project_list(self):
        """测试项目列表"""
        print("\n📁 测试项目列表...")
        try:
            resp = requests.get("http://localhost:8200/api/v1/projects",
                               headers={"X-USER-ID": "u1"})
            if resp.status_code == 200:
                projects = resp.json()
                print(f"✅ 获取项目列表成功: {len(projects)} 个项目")
                if projects:
                    return projects[0]["id"]
                else:
                    # 创建默认项目
                    create_resp = requests.post(
                        "http://localhost:8200/api/v1/projects",
                        json={"name": "Test Project", "description": "测试项目"},
                        headers={"X-USER-ID": "u1"}
                    )
                    if create_resp.status_code == 200:
                        project = create_resp.json()
                        print(f"✅ 创建默认项目成功: {project['id']}")
                        return project["id"]
            return None
        except Exception as e:
            print(f"❌ 项目列表测试失败: {e}")
            return None
    
    def test_document_upload(self, project_id):
        """测试文档上传"""
        print("\n📄 测试文档上传...")
        
        # 创建测试文件
        test_content = """
# AI技术测试文档

这是一个测试文档，用于验证DPA系统功能。

## 主要内容

1. **人工智能**：包括机器学习、深度学习等技术
2. **自然语言处理**：文本理解、生成和翻译
3. **计算机视觉**：图像识别和处理

## 关键技术

- OpenAI的GPT系列模型
- Google的BERT和Transformer架构
- 深度神经网络

## 应用场景

人工智能技术正在医疗、金融、教育等领域广泛应用。
"""
        
        test_file = Path("test_doc.txt")
        test_file.write_text(test_content)
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': ('test_doc.txt', f, 'text/plain')}
                resp = requests.post(
                    f"http://localhost:8200/api/v1/documents/upload?project_id={project_id}",
                    files=files,
                    headers={"X-USER-ID": "u1"}
                )
                
            if resp.status_code == 200:
                result = resp.json()
                doc_id = result.get("document_id")
                print(f"✅ 文档上传成功: {doc_id}")
                return doc_id
            else:
                print(f"❌ 文档上传失败: {resp.status_code} - {resp.text}")
                return None
                
        except Exception as e:
            print(f"❌ 文档上传异常: {e}")
            return None
        finally:
            test_file.unlink(missing_ok=True)
    
    def test_summary_generation(self, document_id):
        """测试摘要生成"""
        print("\n📝 测试摘要生成...")
        
        try:
            # 启动摘要生成
            resp = requests.post(
                f"http://localhost:8200/api/v1/documents/{document_id}/operations/start",
                json={"operation_types": ["summary"]},
                headers={"X-USER-ID": "u1"}
            )
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ 摘要生成已启动: {result.get('pipeline_id')}")
                
                # 等待处理
                print("⏳ 等待摘要生成...", end="")
                for i in range(20):
                    time.sleep(1)
                    print(".", end="", flush=True)
                
                # 获取摘要
                summary_resp = requests.get(
                    f"http://localhost:8200/api/v1/documents/{document_id}/summary",
                    headers={"X-USER-ID": "u1"}
                )
                
                if summary_resp.status_code == 200:
                    summary = summary_resp.json()
                    print(f"\n✅ 摘要生成成功")
                    print(f"   摘要内容: {summary.get('summary', '')[:100]}...")
                    return True
                else:
                    print(f"\n❌ 获取摘要失败: {summary_resp.status_code}")
                    return False
            else:
                print(f"❌ 启动摘要生成失败: {resp.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 摘要生成异常: {e}")
            return False
    
    def test_qa_system(self, project_id):
        """测试问答系统"""
        print("\n❓ 测试问答系统...")
        
        try:
            questions = [
                "这个文档的主要内容是什么？",
                "文档中提到了哪些AI技术？",
                "GPT模型是哪家公司开发的？"
            ]
            
            for question in questions:
                resp = requests.post(
                    "http://localhost:8200/api/v1/qa/answer",
                    json={
                        "project_id": project_id,
                        "question": question
                    },
                    headers={"X-USER-ID": "u1"}
                )
                
                if resp.status_code == 200:
                    answer = resp.json()
                    print(f"✅ 问题: {question}")
                    print(f"   回答: {answer.get('answer', '')[:100]}...")
                else:
                    print(f"❌ 问答失败: {question}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ 问答系统异常: {e}")
            return False
    
    def cleanup(self):
        """清理进程"""
        print("\n🧹 清理进程...")
        
        if self.backend_pid:
            subprocess.run(["kill", str(self.backend_pid)])
            print("✅ 后端服务已停止")
        
        if self.frontend_pid:
            subprocess.run(["kill", str(self.frontend_pid)])
            print("✅ 前端服务已停止")
        
        # 清理临时文件
        Path("start_backend_temp.sh").unlink(missing_ok=True)
        Path("start_frontend_temp.sh").unlink(missing_ok=True)
    
    def run(self):
        """运行测试"""
        print("🚀 DPA系统自动化集成测试")
        print("="*50)
        print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        try:
            # 启动服务
            if not self.start_backend():
                return
            
            if not self.start_frontend():
                return
            
            # 等待服务稳定
            print("\n⏳ 等待服务稳定...")
            time.sleep(3)
            
            # 执行测试
            results = []
            
            # 健康检查
            results.append(("健康检查", self.test_health_check()))
            
            # 项目列表
            project_id = self.test_project_list()
            results.append(("项目管理", project_id is not None))
            
            if project_id:
                # 文档上传
                doc_id = self.test_document_upload(project_id)
                results.append(("文档上传", doc_id is not None))
                
                if doc_id:
                    # 摘要生成
                    results.append(("摘要生成", self.test_summary_generation(doc_id)))
                
                # 问答系统
                results.append(("问答系统", self.test_qa_system(project_id)))
            
            # 打印总结
            print("\n" + "="*50)
            print("📊 测试总结")
            print("="*50)
            
            success_count = sum(1 for _, passed in results if passed)
            total_count = len(results)
            
            for name, passed in results:
                status = "✅ 通过" if passed else "❌ 失败"
                print(f"{name}: {status}")
            
            print(f"\n总计: {success_count}/{total_count} 通过")
            print("="*50)
            
        except KeyboardInterrupt:
            print("\n⚠️ 测试被中断")
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
        finally:
            self.cleanup()
            print(f"\n结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    tester = SimpleDPATest()
    tester.run()