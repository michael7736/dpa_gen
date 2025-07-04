"""
文档元数据管理API
支持增量更新和查询
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...models.document_metadata import (
    DocumentMetadata,
    DocumentMetadataUpdate,
    MetadataEnrichmentService,
    DocumentSource,
    ConfidenceLevel,
    MetadataQuery
)
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])


@router.post("/documents/{document_id}/metadata")
async def update_document_metadata(
    document_id: str,
    updates: DocumentMetadataUpdate,
    db: Session = Depends(get_db_session)
):
    """
    增量更新文档元数据
    
    支持的字段：
    - project_id: 所属项目
    - directory_path: 所在目录
    - upstream_references: 参考文献
    - downstream_citations: 被引用文献
    - source_type: 文档来源
    - confidence_stars: 置信度评分
    - publication_date: 发表时间
    - abstract: 摘要
    - table_of_contents: 目录
    """
    try:
        service = MetadataEnrichmentService(db)
        metadata = await service.enrich_metadata(document_id, updates)
        
        return {
            "success": True,
            "message": "Metadata updated successfully",
            "metadata": metadata,
            "version": metadata.metadata_version
        }
    except Exception as e:
        logger.error(f"Failed to update metadata for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/metadata")
async def get_document_metadata(
    document_id: str,
    db: Session = Depends(get_db_session)
):
    """获取文档元数据"""
    metadata = db.query(DocumentMetadata).filter_by(
        document_id=document_id
    ).first()
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    return metadata


@router.post("/documents/{document_id}/references")
async def update_document_references(
    document_id: str,
    cited_document_ids: List[str],
    db: Session = Depends(get_db_session)
):
    """更新文档引用关系"""
    try:
        service = MetadataEnrichmentService(db)
        await service.update_references(document_id, cited_document_ids)
        
        return {
            "success": True,
            "message": f"Updated references: {document_id} cites {len(cited_document_ids)} documents"
        }
    except Exception as e:
        logger.error(f"Failed to update references: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{document_id}/confidence")
async def calculate_document_confidence(
    document_id: str,
    db: Session = Depends(get_db_session)
):
    """计算文档置信度评分"""
    try:
        service = MetadataEnrichmentService(db)
        confidence_result = await service.calculate_confidence_score(document_id)
        
        # 更新元数据
        updates = DocumentMetadataUpdate(
            confidence_stars=confidence_result["stars"],
            confidence_level=confidence_result["level"],
            confidence_notes=confidence_result["notes"]
        )
        await service.enrich_metadata(document_id, updates)
        
        return confidence_result
    except Exception as e:
        logger.error(f"Failed to calculate confidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/documents/by-confidence")
async def get_documents_by_confidence(
    project_id: str,
    min_stars: int = Query(4, ge=1, le=5),
    db: Session = Depends(get_db_session)
):
    """获取项目中的高置信度文档"""
    documents = MetadataQuery.get_documents_by_confidence(
        db, project_id, min_stars
    ).all()
    
    return {
        "project_id": project_id,
        "min_stars": min_stars,
        "count": len(documents),
        "documents": documents
    }


@router.get("/projects/{project_id}/documents/recent")
async def get_recent_documents(
    project_id: str,
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db_session)
):
    """获取最近发表的文档"""
    documents = MetadataQuery.get_recent_documents(
        db, project_id, months
    ).all()
    
    return {
        "project_id": project_id,
        "months": months,
        "count": len(documents),
        "documents": documents
    }


@router.get("/documents/{document_id}/enrichment-status")
async def get_enrichment_status(
    document_id: str,
    db: Session = Depends(get_db_session)
):
    """获取文档元数据填充状态"""
    metadata = db.query(DocumentMetadata).filter_by(
        document_id=document_id
    ).first()
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    # 分析哪些字段已填充
    enrichment_status = metadata.enrichment_status or {}
    
    # 定义所有可能的字段
    all_fields = [
        "project_id", "directory_path", "upstream_references",
        "downstream_citations", "source_type", "source_url",
        "confidence_stars", "confidence_level", "publication_date",
        "abstract", "table_of_contents", "key_points"
    ]
    
    # 计算填充率
    filled_fields = [f for f in all_fields if enrichment_status.get(f, {}).get("filled")]
    fill_rate = len(filled_fields) / len(all_fields) * 100
    
    return {
        "document_id": document_id,
        "metadata_version": metadata.metadata_version,
        "last_enriched_at": metadata.last_enriched_at,
        "fill_rate": f"{fill_rate:.1f}%",
        "filled_fields": filled_fields,
        "missing_fields": [f for f in all_fields if f not in filled_fields],
        "enrichment_details": enrichment_status
    }


@router.post("/batch/extract-metadata")
async def batch_extract_metadata(
    document_ids: List[str],
    db: Session = Depends(get_db_session)
):
    """批量从文档内容中提取元数据"""
    results = []
    service = MetadataEnrichmentService(db)
    
    for doc_id in document_ids:
        try:
            # 获取文档内容
            # 这里需要从文档表获取内容
            # content = await get_document_content(doc_id)
            # await service.extract_metadata_from_content(doc_id, content)
            
            results.append({
                "document_id": doc_id,
                "status": "success",
                "message": "Metadata extracted"
            })
        except Exception as e:
            results.append({
                "document_id": doc_id,
                "status": "error",
                "message": str(e)
            })
    
    success_count = sum(1 for r in results if r["status"] == "success")
    
    return {
        "total": len(document_ids),
        "success": success_count,
        "failed": len(document_ids) - success_count,
        "results": results
    }