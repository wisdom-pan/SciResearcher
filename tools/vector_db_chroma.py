"""
向量数据库模块
使用ChromaDB + 魔搭Embedding API
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
import uuid


class VectorDB:
    """基于ChromaDB的向量数据库"""

    def __init__(self, collection_name: str = "papers"):
        """初始化向量数据库"""
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            print("警告: chromadb 未安装，请运行: pip install chromadb")
            # 创建一个简单的fallback实现
            self.collection = None
            self.openai_client = None
            return

        self.client = chromadb.PersistentClient(path="./data/chromadb")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.openai_client = OpenAI(
            api_key=os.getenv("MODELSCOPE_API_KEY"),
            base_url=os.getenv("MODELSCOPE_BASE_URL")
        )

    def embed_text(self, text: str) -> List[float]:
        """使用魔搭API生成文本向量"""
        if not self.openai_client:
            print("警告: OpenAI客户端未初始化")
            # 返回随机向量作为fallback
            import random
            return [random.random() for _ in range(1536)]

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-v3",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"嵌入生成失败: {e}")
            # 返回随机向量作为fallback
            import random
            return [random.random() for _ in range(1536)]

    def add_document(self, doc_id: str, content: str, metadata: Dict = None):
        """添加文档到数据库"""
        if not self.collection:
            print("ChromaDB未初始化，无法添加文档")
            return False

        # 分块
        chunks = self._chunk_text(content)

        if not chunks:
            return False

        # 为每个块生成嵌入
        print(f"正在为文档 '{doc_id}' 生成 {len(chunks)} 个嵌入...")
        embeddings = [self.embed_text(chunk) for chunk in chunks]

        # 准备数据
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {**(metadata or {}), "chunk_index": i, "doc_id": doc_id}
            for i in range(len(chunks))
        ]

        # 添加到ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        print(f"✓ 成功添加文档 '{doc_id}' ({len(chunks)} 个块)")
        return True

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """搜索相关文档"""
        if not self.collection:
            print("ChromaDB未初始化，无法搜索")
            return []

        # 生成查询向量
        query_embedding = self.embed_text(query)

        # 搜索
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            # 格式化结果
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                formatted_results.append({
                    "content": doc,
                    "metadata": metadata,
                    "score": 1 - distance  # 转换为相似度
                })

            return formatted_results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """将文本分块"""
        if not text:
            return []

        chunks = []
        start = 0
        text = text.replace('\n', ' ')

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # 尝试在句号处分割
            if end < len(text):
                last_period = text.rfind('。', start, end)
                if last_period > start:
                    end = last_period + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = max(start + chunk_size - overlap, end)

        return chunks

    def list_documents(self) -> List[Dict]:
        """列出所有文档"""
        if not self.collection:
            return []

        try:
            # 获取所有文档ID
            all_data = self.collection.get()
            doc_ids = set()
            for metadata in all_data['metadatas']:
                doc_ids.add(metadata['doc_id'])

            # 获取每个文档的信息
            docs = []
            for doc_id in doc_ids:
                # 获取该文档的所有块
                results = self.collection.get(
                    where={"doc_id": doc_id},
                    include=['metadatas']
                )

                if results['metadatas']:
                    docs.append({
                        "doc_id": doc_id,
                        "chunk_count": len(results['metadatas']),
                        "sample_metadata": results['metadatas'][0]
                    })

            return docs
        except Exception as e:
            print(f"列出文档失败: {e}")
            return []

    def delete_document(self, doc_id: str):
        """删除文档"""
        if not self.collection:
            return False

        try:
            # 获取该文档的所有块ID
            results = self.collection.get(
                where={"doc_id": doc_id},
                include=['ids']
            )

            if results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"✓ 已删除文档 '{doc_id}'")
                return True

            return False
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False

    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        if not self.collection:
            return {"error": "ChromaDB未初始化"}

        try:
            count = self.collection.count()
            docs = self.list_documents()
            return {
                "total_chunks": count,
                "total_documents": len(docs),
                "documents": docs
            }
        except Exception as e:
            return {"error": str(e)}


# 全局向量数据库实例
vector_db = VectorDB()
