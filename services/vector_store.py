"""
向量存储服务 (ChromaDB)
"""
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

class VectorStore:
    """ChromaDB 向量存储 (单例)"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, embedding_service, index_dir: str = "./data/vector_index"):
        if self._initialized:
            return

        self.embedding_service = embedding_service
        self.dimension = embedding_service.dimension

        # 初始化 ChromaDB 客户端
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.index_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 创建或获取集合
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"dimension": self.dimension}
        )

        print(f"📂 ChromaDB 已初始化: {self.collection.count()} 个向量")
        self._initialized = True

    def add_texts(self, texts: List[str], metadata: Optional[List[Dict]] = None):
        """批量添加文本"""
        if not texts:
            return

        print(f"📊 向量化 {len(texts)} 个文本块...")

        # 生成向量
        embeddings = [self.embedding_service.embed(text) for text in texts]

        # 生成ID
        current_count = self.collection.count()
        ids = [f"doc_{current_count + i}" for i in range(len(texts))]

        # 准备元数据
        if metadata is None:
            metadata = [{"index": current_count + i} for i in range(len(texts))]

        # 添加到 ChromaDB
        self.collection.add(
            embeddings=[emb.tolist() for emb in embeddings],
            documents=texts,
            metadatas=metadata,
            ids=ids
        )

        print(f"✅ 成功添加 {len(texts)} 个向量")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义搜索"""
        if self.collection.count() == 0:
            return []

        # 查询向量化
        query_vector = self.embedding_service.embed(query)

        # ChromaDB 搜索
        results = self.collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=min(top_k, self.collection.count())
        )

        # 构建结果
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "score": results['distances'][0][i] if 'distances' in results else 0.0,
                    "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                })

        return formatted_results

    def save(self):
        """保存索引 (ChromaDB 自动持久化)"""
        count = self.collection.count()
        print(f"💾 索引已保存: {count} 个向量 (ChromaDB 自动持久化)")

    def reset(self):
        """清空集合"""
        self.client.delete_collection("documents")
        self.collection = self.client.create_collection(
            name="documents",
            metadata={"dimension": self.dimension}
        )
        print("🗑️ 向量库已清空")
