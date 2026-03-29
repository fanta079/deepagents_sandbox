"""
RAG 相关 API - 文档向量化和检索
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.vector_store import get_vector_store, MILVUS_AVAILABLE

router = APIRouter(prefix="/rag", tags=["RAG"])


class AddDocsRequest(BaseModel):
    texts: list[str]
    metadatas: list[dict] | None = None


class SearchRequest(BaseModel):
    query: str
    k: int = 4


@router.post("/add")
async def add_documents(request: AddDocsRequest):
    """添加文档到向量库"""
    if not MILVUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vector store not available")

    vs = get_vector_store()
    ids = vs.add_documents(request.texts, request.metadatas)
    return {"ids": ids, "count": len(ids)}


@router.post("/search")
async def search_documents(request: SearchRequest):
    """检索相似文档"""
    if not MILVUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vector store not available")

    vs = get_vector_store()
    docs = vs.similarity_search(request.query, k=request.k)
    return {
        "results": [{"content": d.page_content, "metadata": d.metadata} for d in docs]
    }


@router.get("/health")
async def rag_health():
    """RAG 健康检查"""
    return {"available": MILVUS_AVAILABLE, "status": "ok" if MILVUS_AVAILABLE else "disabled"}
