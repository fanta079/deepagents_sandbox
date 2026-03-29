"""
Milvus 向量数据库支持 - RAG 能力

用于：
- 文档向量化和存储
- 相似文档检索
- Agent 知识增强
"""
from typing import Any
import logging

logger = logging.getLogger(__name__)

try:
    from langchain_community.vectorstores import Milvus
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("Milvus or langchain not installed, vector store disabled")


class VectorStore:
    """向量存储管理器"""

    def __init__(self, connection_uri: str = "http://localhost:19530"):
        if not MILVUS_AVAILABLE:
            raise RuntimeError("Milvus not available, install milvus-lite and pymilvus")

        self.connection_uri = connection_uri
        self.embeddings = None
        self.vectorstore = None

    def initialize(self, collection_name: str = "deepagents_docs"):
        """初始化向量存储"""
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = Milvus(
            embedding_function=self.embeddings,
            connection_address=self.connection_uri,
            collection_name=collection_name,
        )
        logger.info(f"Vector store initialized: {collection_name}")

    def add_documents(self, texts: list[str], metadatas: list[dict] | None = None):
        """添加文档到向量库"""
        if not self.vectorstore:
            self.initialize()
        return self.vectorstore.add_texts(texts, metadatas=metadatas)

    def similarity_search(self, query: str, k: int = 4) -> list[Any]:
        """相似文档检索"""
        if not self.vectorstore:
            return []
        return self.vectorstore.similarity_search(query, k=k)

    def delete_collection(self, collection_name: str):
        """删除集合"""
        from pymilvus import connections, Collection

        connections.connect(uri=self.connection_uri)
        collection = Collection(collection_name)
        collection.drop()


# 全局实例（延迟初始化）
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
