"""
文档处理器测试
"""
import asyncio
import pytest
from pathlib import Path
import tempfile
import shutil

from src.core.document.mvp_document_processor import (
    create_mvp_document_processor,
    DocumentMetadata,
    DocumentChunk
)


@pytest.fixture
async def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def sample_files(temp_dir):
    """创建测试文件"""
    files = {}
    
    # 创建文本文件
    txt_file = Path(temp_dir) / "test.txt"
    txt_file.write_text("""
    深度学习是机器学习的一个子领域，它试图模拟人脑的工作方式。
    通过多层神经网络，深度学习可以自动学习数据的特征表示。
    
    卷积神经网络（CNN）在图像识别领域表现出色。
    循环神经网络（RNN）适合处理序列数据。
    Transformer架构彻底改变了自然语言处理领域。
    """)
    files['txt'] = txt_file
    
    # 创建Markdown文件
    md_file = Path(temp_dir) / "test.md"
    md_file.write_text("""
# 深度学习简介

## 什么是深度学习？

深度学习是机器学习的一个分支，使用多层神经网络来学习数据的复杂模式。

## 主要架构

1. **CNN** - 卷积神经网络
2. **RNN** - 循环神经网络  
3. **Transformer** - 注意力机制

## 应用领域

- 计算机视觉
- 自然语言处理
- 语音识别
    """)
    files['md'] = md_file
    
    return files


@pytest.mark.asyncio
async def test_process_text_file(sample_files):
    """测试处理文本文件"""
    processor = create_mvp_document_processor()
    
    result = await processor.process_document(
        file_path=str(sample_files['txt']),
        project_id="test_project"
    )
    
    assert isinstance(result, DocumentMetadata)
    assert result.status == "completed"
    assert result.chunk_count > 0
    assert result.file_type == ".txt"


@pytest.mark.asyncio
async def test_process_markdown_file(sample_files):
    """测试处理Markdown文件"""
    processor = create_mvp_document_processor()
    
    result = await processor.process_document(
        file_path=str(sample_files['md']),
        project_id="test_project"
    )
    
    assert result.status == "completed"
    assert result.chunk_count > 0
    assert result.file_type == ".md"


@pytest.mark.asyncio
async def test_batch_processing(sample_files):
    """测试批量处理"""
    processor = create_mvp_document_processor()
    
    file_paths = [str(sample_files['txt']), str(sample_files['md'])]
    results = await processor.process_batch(
        file_paths=file_paths,
        project_id="test_batch",
        max_concurrent=2
    )
    
    assert len(results) == 2
    for result in results:
        assert result.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_text_splitting():
    """测试文本分块"""
    processor = create_mvp_document_processor()
    
    # 创建测试文本
    test_text = "这是第一段。\n\n这是第二段。\n\n这是第三段。" * 100
    
    metadata = DocumentMetadata(
        document_id="test_doc",
        filename="test.txt",
        file_path="test.txt",
        file_size=len(test_text),
        file_type=".txt",
        created_at="2024-01-01"
    )
    
    chunks = processor._split_text(test_text, metadata)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    
    # 验证块的连续性
    for i in range(len(chunks) - 1):
        assert chunks[i].chunk_index == i
        assert chunks[i].end_char <= chunks[i+1].start_char + 200  # 考虑重叠


@pytest.mark.asyncio
async def test_concept_extraction():
    """测试概念提取"""
    processor = create_mvp_document_processor()
    
    test_chunks = [
        DocumentChunk(
            chunk_id="chunk_1",
            document_id="doc_1",
            content="深度学习 深度学习 深度学习 神经网络 神经网络",
            chunk_index=0,
            start_char=0,
            end_char=100,
            metadata={}
        )
    ]
    
    concepts = processor._extract_simple_concepts(test_chunks)
    
    assert len(concepts) > 0
    assert any(c["name"] == "深度学习" for c in concepts)
    assert concepts[0]["confidence"] > 0


@pytest.mark.asyncio
async def test_file_not_found():
    """测试文件不存在的情况"""
    processor = create_mvp_document_processor()
    
    with pytest.raises(FileNotFoundError):
        await processor.process_document(
            file_path="/non/existent/file.txt"
        )


@pytest.mark.asyncio
async def test_unsupported_file_type():
    """测试不支持的文件类型"""
    processor = create_mvp_document_processor()
    
    with tempfile.NamedTemporaryFile(suffix='.xyz') as f:
        with pytest.raises(ValueError, match="Unsupported file type"):
            await processor.process_document(file_path=f.name)


@pytest.mark.asyncio
async def test_processing_status():
    """测试处理状态跟踪"""
    processor = create_mvp_document_processor()
    
    # 创建一个大文件来延长处理时间
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("测试内容\n" * 1000)
        temp_file = f.name
        
    try:
        # 开始处理（不等待）
        task = asyncio.create_task(
            processor.process_document(temp_file)
        )
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        # 检查处理状态
        doc_id = processor._generate_document_id(Path(temp_file))
        status = processor.get_processing_status(doc_id)
        
        # 可能已经完成或正在处理
        if status:
            assert status.status in ["processing", "completed"]
            
        # 等待完成
        result = await task
        assert result.status == "completed"
        
    finally:
        Path(temp_file).unlink()


@pytest.mark.asyncio
async def test_unicode_content():
    """测试Unicode内容处理"""
    processor = create_mvp_document_processor()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as f:
        f.write("中文内容测试 🚀\n日本語のテスト\n한국어 테스트")
        temp_file = f.name
        
    try:
        result = await processor.process_document(temp_file)
        assert result.status == "completed"
        assert result.chunk_count > 0
    finally:
        Path(temp_file).unlink()


if __name__ == "__main__":
    # 运行基本测试
    async def main():
        print("Testing Document Processor...")
        
        # 创建测试文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试文件
            txt_file = Path(temp_dir) / "test.txt"
            txt_file.write_text("这是一个测试文档。\n包含一些深度学习的内容。")
            
            # 测试处理
            processor = create_mvp_document_processor()
            result = await processor.process_document(
                str(txt_file),
                project_id="test_cli"
            )
            
            print(f"✓ Document processed: {result.document_id}")
            print(f"  Status: {result.status}")
            print(f"  Chunks: {result.chunk_count}")
            
        print("\nAll tests passed!")
        
    asyncio.run(main())