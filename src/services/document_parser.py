"""
文档解析服务
支持多种文档格式的解析和结构提取
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

# PDF解析
import fitz  # PyMuPDF
import pdfplumber
from pypdf import PdfReader

# DOCX解析
from docx import Document as DocxDocument
from docx.shared import Inches

# Markdown解析
import markdown
from markdown.extensions import toc
from bs4 import BeautifulSoup

# 表格提取
import camelot
import pandas as pd

# OCR支持
try:
    import paddleocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# 图像处理
from PIL import Image
import io

logger = logging.getLogger(__name__)

@dataclass
class DocumentSection:
    """文档章节"""
    id: str
    title: str
    level: int  # 标题层级 (1-6)
    content: str
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    subsections: List['DocumentSection'] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []

@dataclass
class DocumentTable:
    """文档表格"""
    id: str
    caption: str
    data: pd.DataFrame
    page_number: int
    bbox: Optional[tuple] = None  # (x1, y1, x2, y2)

@dataclass
class DocumentFigure:
    """文档图片/图表"""
    id: str
    caption: str
    image_path: str
    page_number: int
    bbox: Optional[tuple] = None
    ocr_text: Optional[str] = None

@dataclass
class DocumentReference:
    """文档引用"""
    id: str
    text: str
    url: Optional[str] = None
    doi: Optional[str] = None

@dataclass
class DocumentMetadata:
    """文档元数据"""
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    keywords: List[str] = None
    publication_date: Optional[datetime] = None
    doi: Optional[str] = None
    source: Optional[str] = None
    language: str = "en"
    page_count: int = 0

@dataclass
class ParsedDocument:
    """解析后的文档"""
    metadata: DocumentMetadata
    sections: List[DocumentSection]
    tables: List[DocumentTable]
    figures: List[DocumentFigure]
    references: List[DocumentReference]
    raw_text: str
    processing_info: Dict[str, Any]

class BaseDocumentParser(ABC):
    """文档解析器基类"""
    
    @abstractmethod
    async def parse(self, file_path: str) -> ParsedDocument:
        """解析文档"""
        pass
    
    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """检查是否支持该格式"""
        pass

class PDFParser(BaseDocumentParser):
    """PDF文档解析器"""
    
    def __init__(self):
        self.ocr_engine = None
        if OCR_AVAILABLE:
            self.ocr_engine = paddleocr.PaddleOCR(use_angle_cls=True, lang='ch')
    
    def supports_format(self, file_extension: str) -> bool:
        return file_extension.lower() == '.pdf'
    
    async def parse(self, file_path: str) -> ParsedDocument:
        """解析PDF文档"""
        logger.info(f"开始解析PDF文档: {file_path}")
        
        try:
            # 使用多种方法解析PDF
            pymupdf_result = await self._parse_with_pymupdf(file_path)
            pdfplumber_result = await self._parse_with_pdfplumber(file_path)
            
            # 合并解析结果
            merged_result = await self._merge_pdf_results(
                pymupdf_result, pdfplumber_result, file_path
            )
            
            logger.info(f"PDF解析完成: {len(merged_result.sections)}个章节")
            return merged_result
            
        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            raise
    
    async def _parse_with_pymupdf(self, file_path: str) -> Dict[str, Any]:
        """使用PyMuPDF解析PDF"""
        doc = fitz.open(file_path)
        
        result = {
            'text': '',
            'sections': [],
            'figures': [],
            'metadata': {},
            'toc': []
        }
        
        # 提取元数据
        metadata = doc.metadata
        result['metadata'] = {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', ''),
            'page_count': doc.page_count
        }
        
        # 提取目录
        toc = doc.get_toc()
        result['toc'] = toc
        
        # 逐页提取内容
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # 提取文本
            text = page.get_text()
            result['text'] += f"\n--- Page {page_num + 1} ---\n{text}"
            
            # 提取图片
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # 确保是RGB或灰度图
                        img_data = pix.tobytes("png")
                        img_path = f"temp/page_{page_num + 1}_img_{img_index}.png"
                        
                        # 保存图片
                        with open(img_path, "wb") as f:
                            f.write(img_data)
                        
                        # OCR识别图片中的文字
                        ocr_text = ""
                        if self.ocr_engine:
                            try:
                                ocr_result = self.ocr_engine.ocr(img_path, cls=True)
                                if ocr_result and ocr_result[0]:
                                    ocr_text = " ".join([line[1][0] for line in ocr_result[0]])
                            except Exception as e:
                                logger.warning(f"OCR识别失败: {e}")
                        
                        result['figures'].append({
                            'page': page_num + 1,
                            'index': img_index,
                            'path': img_path,
                            'ocr_text': ocr_text
                        })
                    
                    pix = None
                except Exception as e:
                    logger.warning(f"图片提取失败: {e}")
        
        doc.close()
        return result
    
    async def _parse_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """使用pdfplumber解析PDF（更好的表格提取）"""
        result = {
            'tables': [],
            'text_with_layout': '',
            'pages_info': []
        }
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_info = {
                    'page_number': page_num + 1,
                    'width': page.width,
                    'height': page.height,
                    'text': page.extract_text() or '',
                    'tables': []
                }
                
                # 提取表格
                tables = page.extract_tables()
                for table_index, table in enumerate(tables):
                    if table:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        result['tables'].append({
                            'page': page_num + 1,
                            'index': table_index,
                            'data': df,
                            'bbox': None  # pdfplumber可以提供bbox信息
                        })
                        page_info['tables'].append(table_index)
                
                result['pages_info'].append(page_info)
                result['text_with_layout'] += f"\n--- Page {page_num + 1} ---\n{page_info['text']}"
        
        return result
    
    async def _merge_pdf_results(
        self, 
        pymupdf_result: Dict[str, Any], 
        pdfplumber_result: Dict[str, Any],
        file_path: str
    ) -> ParsedDocument:
        """合并不同解析器的结果"""
        
        # 构建元数据
        metadata = DocumentMetadata(
            title=pymupdf_result['metadata'].get('title', Path(file_path).stem),
            authors=[pymupdf_result['metadata'].get('author', '')] if pymupdf_result['metadata'].get('author') else [],
            page_count=pymupdf_result['metadata'].get('page_count', 0),
            source=file_path
        )
        
        # 构建章节结构
        sections = await self._build_sections_from_toc(
            pymupdf_result['toc'], 
            pymupdf_result['text']
        )
        
        # 构建表格列表
        tables = []
        for table_info in pdfplumber_result['tables']:
            table = DocumentTable(
                id=f"table_{table_info['page']}_{table_info['index']}",
                caption=f"Table on page {table_info['page']}",
                data=table_info['data'],
                page_number=table_info['page'],
                bbox=table_info.get('bbox')
            )
            tables.append(table)
        
        # 构建图片列表
        figures = []
        for fig_info in pymupdf_result['figures']:
            figure = DocumentFigure(
                id=f"figure_{fig_info['page']}_{fig_info['index']}",
                caption=f"Figure on page {fig_info['page']}",
                image_path=fig_info['path'],
                page_number=fig_info['page'],
                ocr_text=fig_info.get('ocr_text', '')
            )
            figures.append(figure)
        
        # 提取引用（简单实现）
        references = await self._extract_references(pymupdf_result['text'])
        
        return ParsedDocument(
            metadata=metadata,
            sections=sections,
            tables=tables,
            figures=figures,
            references=references,
            raw_text=pymupdf_result['text'],
            processing_info={
                'parser': 'PDFParser',
                'methods': ['PyMuPDF', 'pdfplumber'],
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def _build_sections_from_toc(self, toc: List, full_text: str) -> List[DocumentSection]:
        """从目录构建章节结构"""
        sections = []
        
        if not toc:
            # 如果没有目录，尝试从文本中提取标题
            return await self._extract_sections_from_text(full_text)
        
        for i, (level, title, page) in enumerate(toc):
            section_id = f"section_{i}"
            
            # 提取章节内容（简化实现）
            content = await self._extract_section_content(title, full_text)
            
            section = DocumentSection(
                id=section_id,
                title=title.strip(),
                level=level,
                content=content,
                start_page=page
            )
            sections.append(section)
        
        return sections
    
    async def _extract_sections_from_text(self, text: str) -> List[DocumentSection]:
        """从文本中提取章节（当没有目录时）"""
        import re
        
        sections = []
        
        # 简单的标题识别模式
        title_patterns = [
            r'^(\d+\.?\s+.+)$',  # 数字开头的标题
            r'^([A-Z][A-Z\s]+)$',  # 全大写标题
            r'^(Abstract|Introduction|Conclusion|References)$',  # 常见章节
        ]
        
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是标题
            is_title = False
            for pattern in title_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_title = True
                    break
            
            if is_title:
                # 保存前一个章节
                if current_section:
                    current_section.content = '\n'.join(section_content)
                    sections.append(current_section)
                
                # 开始新章节
                current_section = DocumentSection(
                    id=f"section_{len(sections)}",
                    title=line,
                    level=1,
                    content=""
                )
                section_content = []
            else:
                section_content.append(line)
        
        # 保存最后一个章节
        if current_section:
            current_section.content = '\n'.join(section_content)
            sections.append(current_section)
        
        return sections
    
    async def _extract_section_content(self, title: str, full_text: str) -> str:
        """提取特定章节的内容"""
        # 简化实现：查找标题后的内容
        lines = full_text.split('\n')
        content_lines = []
        found_title = False
        
        for line in lines:
            if title.lower() in line.lower() and not found_title:
                found_title = True
                continue
            
            if found_title:
                # 如果遇到下一个标题，停止
                if line.strip() and (
                    line.strip().isupper() or 
                    line.strip().startswith(('1.', '2.', '3.', '4.', '5.'))
                ):
                    break
                content_lines.append(line)
        
        return '\n'.join(content_lines[:100])  # 限制长度
    
    async def _extract_references(self, text: str) -> List[DocumentReference]:
        """提取文档引用"""
        import re
        
        references = []
        
        # 查找References章节
        ref_section = re.search(r'References\s*\n(.*?)(?:\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
        if not ref_section:
            return references
        
        ref_text = ref_section.group(1)
        
        # 简单的引用提取（可以改进）
        ref_lines = ref_text.split('\n')
        for i, line in enumerate(ref_lines):
            line = line.strip()
            if line and len(line) > 20:  # 过滤太短的行
                ref = DocumentReference(
                    id=f"ref_{i}",
                    text=line,
                    url=self._extract_url_from_text(line),
                    doi=self._extract_doi_from_text(line)
                )
                references.append(ref)
        
        return references
    
    def _extract_url_from_text(self, text: str) -> Optional[str]:
        """从文本中提取URL"""
        import re
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None
    
    def _extract_doi_from_text(self, text: str) -> Optional[str]:
        """从文本中提取DOI"""
        import re
        doi_pattern = r'10\.\d+/[^\s]+'
        match = re.search(doi_pattern, text)
        return match.group(0) if match else None

class DOCXParser(BaseDocumentParser):
    """DOCX文档解析器"""
    
    def supports_format(self, file_extension: str) -> bool:
        return file_extension.lower() == '.docx'
    
    async def parse(self, file_path: str) -> ParsedDocument:
        """解析DOCX文档"""
        logger.info(f"开始解析DOCX文档: {file_path}")
        
        try:
            doc = DocxDocument(file_path)
            
            # 提取元数据
            metadata = self._extract_docx_metadata(doc, file_path)
            
            # 提取章节
            sections = await self._extract_docx_sections(doc)
            
            # 提取表格
            tables = self._extract_docx_tables(doc)
            
            # 提取图片
            figures = await self._extract_docx_figures(doc)
            
            # 提取文本
            raw_text = '\n'.join([para.text for para in doc.paragraphs])
            
            # 提取引用
            references = await self._extract_references(raw_text)
            
            return ParsedDocument(
                metadata=metadata,
                sections=sections,
                tables=tables,
                figures=figures,
                references=references,
                raw_text=raw_text,
                processing_info={
                    'parser': 'DOCXParser',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"DOCX解析失败: {e}")
            raise
    
    def _extract_docx_metadata(self, doc: DocxDocument, file_path: str) -> DocumentMetadata:
        """提取DOCX元数据"""
        core_props = doc.core_properties
        
        return DocumentMetadata(
            title=core_props.title or Path(file_path).stem,
            authors=[core_props.author] if core_props.author else [],
            abstract=core_props.subject or None,
            keywords=core_props.keywords.split(',') if core_props.keywords else [],
            publication_date=core_props.created,
            source=file_path,
            page_count=len(doc.paragraphs)  # 近似页数
        )
    
    async def _extract_docx_sections(self, doc: DocxDocument) -> List[DocumentSection]:
        """提取DOCX章节"""
        sections = []
        current_section = None
        section_content = []
        
        for para in doc.paragraphs:
            # 检查是否是标题
            if para.style.name.startswith('Heading'):
                # 保存前一个章节
                if current_section:
                    current_section.content = '\n'.join(section_content)
                    sections.append(current_section)
                
                # 开始新章节
                level = int(para.style.name.split()[-1]) if para.style.name.split()[-1].isdigit() else 1
                current_section = DocumentSection(
                    id=f"section_{len(sections)}",
                    title=para.text,
                    level=level,
                    content=""
                )
                section_content = []
            else:
                if para.text.strip():
                    section_content.append(para.text)
        
        # 保存最后一个章节
        if current_section:
            current_section.content = '\n'.join(section_content)
            sections.append(current_section)
        
        return sections
    
    def _extract_docx_tables(self, doc: DocxDocument) -> List[DocumentTable]:
        """提取DOCX表格"""
        tables = []
        
        for i, table in enumerate(doc.tables):
            # 转换为DataFrame
            data = []
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                data.append(row_data)
            
            if data:
                df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(data)
                
                doc_table = DocumentTable(
                    id=f"table_{i}",
                    caption=f"Table {i + 1}",
                    data=df,
                    page_number=0  # DOCX没有页面概念
                )
                tables.append(doc_table)
        
        return tables
    
    async def _extract_docx_figures(self, doc: DocxDocument) -> List[DocumentFigure]:
        """提取DOCX图片"""
        figures = []
        
        # DOCX图片提取比较复杂，这里提供简化实现
        # 实际实现需要解析document.xml和media文件夹
        
        return figures
    
    async def _extract_references(self, text: str) -> List[DocumentReference]:
        """提取引用（复用PDF的实现）"""
        # 可以复用PDFParser的引用提取逻辑
        pdf_parser = PDFParser()
        return await pdf_parser._extract_references(text)

class MarkdownParser(BaseDocumentParser):
    """Markdown文档解析器"""
    
    def supports_format(self, file_extension: str) -> bool:
        return file_extension.lower() in ['.md', '.markdown']
    
    async def parse(self, file_path: str) -> ParsedDocument:
        """解析Markdown文档"""
        logger.info(f"开始解析Markdown文档: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用markdown库解析
            md = markdown.Markdown(extensions=['toc', 'tables', 'fenced_code'])
            html = md.convert(content)
            
            # 解析HTML获取结构
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取元数据
            metadata = self._extract_markdown_metadata(content, file_path)
            
            # 提取章节
            sections = self._extract_markdown_sections(soup, content)
            
            # 提取表格
            tables = self._extract_markdown_tables(soup)
            
            # 提取图片
            figures = self._extract_markdown_figures(soup, file_path)
            
            # 提取引用
            references = await self._extract_markdown_references(content)
            
            return ParsedDocument(
                metadata=metadata,
                sections=sections,
                tables=tables,
                figures=figures,
                references=references,
                raw_text=content,
                processing_info={
                    'parser': 'MarkdownParser',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Markdown解析失败: {e}")
            raise
    
    def _extract_markdown_metadata(self, content: str, file_path: str) -> DocumentMetadata:
        """提取Markdown元数据"""
        import re
        
        # 查找YAML front matter
        yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        
        title = Path(file_path).stem
        authors = []
        
        if yaml_match:
            yaml_content = yaml_match.group(1)
            # 简单解析YAML（可以使用yaml库改进）
            for line in yaml_content.split('\n'):
                if line.startswith('title:'):
                    title = line.split(':', 1)[1].strip().strip('"\'')
                elif line.startswith('author:'):
                    authors = [line.split(':', 1)[1].strip().strip('"\'')]
        
        return DocumentMetadata(
            title=title,
            authors=authors,
            source=file_path,
            language="en"
        )
    
    def _extract_markdown_sections(self, soup: BeautifulSoup, content: str) -> List[DocumentSection]:
        """提取Markdown章节"""
        sections = []
        
        # 查找所有标题
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for i, heading in enumerate(headings):
            level = int(heading.name[1])  # h1 -> 1, h2 -> 2, etc.
            title = heading.get_text().strip()
            
            # 提取章节内容（简化实现）
            content_text = self._extract_section_content_from_markdown(title, content)
            
            section = DocumentSection(
                id=f"section_{i}",
                title=title,
                level=level,
                content=content_text
            )
            sections.append(section)
        
        return sections
    
    def _extract_section_content_from_markdown(self, title: str, content: str) -> str:
        """从Markdown中提取章节内容"""
        lines = content.split('\n')
        content_lines = []
        found_title = False
        
        for line in lines:
            if title in line and line.startswith('#'):
                found_title = True
                continue
            
            if found_title:
                # 如果遇到同级或更高级标题，停止
                if line.startswith('#'):
                    break
                content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def _extract_markdown_tables(self, soup: BeautifulSoup) -> List[DocumentTable]:
        """提取Markdown表格"""
        tables = []
        
        html_tables = soup.find_all('table')
        for i, table in enumerate(html_tables):
            # 转换HTML表格为DataFrame
            rows = []
            for tr in table.find_all('tr'):
                row = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                if row:
                    rows.append(row)
            
            if rows:
                df = pd.DataFrame(rows[1:], columns=rows[0]) if len(rows) > 1 else pd.DataFrame(rows)
                
                doc_table = DocumentTable(
                    id=f"table_{i}",
                    caption=f"Table {i + 1}",
                    data=df,
                    page_number=0
                )
                tables.append(doc_table)
        
        return tables
    
    def _extract_markdown_figures(self, soup: BeautifulSoup, file_path: str) -> List[DocumentFigure]:
        """提取Markdown图片"""
        figures = []
        
        images = soup.find_all('img')
        for i, img in enumerate(images):
            src = img.get('src', '')
            alt = img.get('alt', f'Figure {i + 1}')
            
            # 处理相对路径
            if src and not src.startswith(('http', 'https')):
                base_dir = Path(file_path).parent
                src = str(base_dir / src)
            
            figure = DocumentFigure(
                id=f"figure_{i}",
                caption=alt,
                image_path=src,
                page_number=0
            )
            figures.append(figure)
        
        return figures
    
    async def _extract_markdown_references(self, content: str) -> List[DocumentReference]:
        """提取Markdown引用"""
        import re
        
        references = []
        
        # 查找链接引用
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, content)
        
        for i, (text, url) in enumerate(matches):
            ref = DocumentReference(
                id=f"ref_{i}",
                text=text,
                url=url
            )
            references.append(ref)
        
        return references

class DocumentParserService:
    """文档解析服务主类"""
    
    def __init__(self):
        self.parsers = {
            '.pdf': PDFParser(),
            '.docx': DOCXParser(),
            '.md': MarkdownParser(),
            '.markdown': MarkdownParser()
        }
    
    async def parse_document(self, file_path: str) -> ParsedDocument:
        """解析文档"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension not in self.parsers:
            raise ValueError(f"不支持的文件格式: {extension}")
        
        parser = self.parsers[extension]
        return await parser.parse(str(file_path))
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return list(self.parsers.keys())
    
    async def batch_parse(self, file_paths: List[str]) -> List[ParsedDocument]:
        """批量解析文档"""
        tasks = [self.parse_document(path) for path in file_paths]
        return await asyncio.gather(*tasks, return_exceptions=True)

# 全局解析器实例
document_parser = DocumentParserService()

# 使用示例
async def example_usage():
    """使用示例"""
    
    # 解析单个文档
    try:
        result = await document_parser.parse_document("example.pdf")
        print(f"解析完成: {result.metadata.title}")
        print(f"章节数: {len(result.sections)}")
        print(f"表格数: {len(result.tables)}")
        print(f"图片数: {len(result.figures)}")
    except Exception as e:
        print(f"解析失败: {e}")
    
    # 批量解析
    files = ["doc1.pdf", "doc2.docx", "doc3.md"]
    results = await document_parser.batch_parse(files)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"文件 {files[i]} 解析失败: {result}")
        else:
            print(f"文件 {files[i]} 解析成功")

if __name__ == "__main__":
    asyncio.run(example_usage())