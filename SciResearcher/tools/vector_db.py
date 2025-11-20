"""
向量数据库 - 使用API进行向量化
"""
import os
import json
import pickle
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from config import get_config

class VectorDatabase:
    """向量数据库，使用API进行Embedding"""

    def __init__(self, index_path: str = None):
        """初始化向量数据库

        Args:
            index_path: 索引文件路径
        """
        config = get_config()

        # 初始化OpenAI客户端 (支持兼容OpenAI的API)
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base_url
        )
        self.embedding_model = config.embedding_model

        # 索引路径
        if index_path is None:
            index_path = config.get('vector_db.index_path', './data/vector_index')

        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)

        # FAISS配置
        self.dimension = config.get('vector_db.dimension', 1536)
        self.index_file = self.index_path / "faiss.index"
        self.texts_file = self.index_path / "texts.pkl"
        self.metadata_file = self.index_path / "metadata.json"

        # 初始化或加载索引
        self.texts = []
        self.metadata = []

        if self.index_file.exists():
            self.load()
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

    def embed(self, text: str) -> np.ndarray:
        """将文本转换为向量

        Args:
            text: 输入文本

        Returns:
            向量数组
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            return np.array(embedding, dtype='float32')

        except Exception as e:
            print(f"Embedding失败: {e}")
            # 返回零向量
            return np.zeros(self.dimension, dtype='float32')

    def add(self, texts: List[str], metadata: List[Dict] = None):
        """添加文本到数据库

        Args:
            texts: 文本列表
            metadata: 元数据列表(可选)
        """
        if not texts:
            return

        print(f"正在向量化 {len(texts)} 个文本块...")

        embeddings = []
        for i, text in enumerate(texts):
            if (i + 1) % 10 == 0:
                print(f"进度: {i + 1}/{len(texts)}")

            embedding = self.embed(text)
            embeddings.append(embedding)

        # 转换为numpy数组
        embeddings = np.array(embeddings).astype('float32')

        # 添加到FAISS索引
        self.index.add(embeddings)

        # 保存文本和元数据
        self.texts.extend(texts)

        if metadata is None:
            metadata = [{"index": len(self.metadata) + i} for i in range(len(texts))]

        self.metadata.extend(metadata)

        print(f"成功添加 {len(texts)} 个文本块")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索最相关的文本

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            结果列表，每个包含 text, score, metadata
        """
        if self.index.ntotal == 0:
            return []

        # 向量化查询
        query_embedding = self.embed(query).reshape(1, -1).astype('float32')

        # 搜索
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        # 构建结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.texts):
                results.append({
                    "text": self.texts[idx],
                    "score": float(distances[0][i]),
                    "metadata": self.metadata[idx] if idx < len(self.metadata) else {}
                })

        return results

    def save(self):
        """保存索引到磁盘"""
        # 保存FAISS索引
        faiss.write_index(self.index, str(self.index_file))

        # 保存文本
        with open(self.texts_file, 'wb') as f:
            pickle.dump(self.texts, f)

        # 保存元数据
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        print(f"索引已保存到 {self.index_path}")

    def load(self):
        """从磁盘加载索引"""
        # 加载FAISS索引
        self.index = faiss.read_index(str(self.index_file))

        # 加载文本
        if self.texts_file.exists():
            with open(self.texts_file, 'rb') as f:
                self.texts = pickle.load(f)

        # 加载元数据
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

        print(f"索引已加载，共 {self.index.ntotal} 个向量")

    def clear(self):
        """清空索引"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.metadata = []

# 文本分块工具
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将长文本分块

    Args:
        text: 输入文本
        chunk_size: 块大小
        overlap: 重叠大小

    Returns:
        文本块列表
    """
    if not text:
        return []

    # 按句子分割
    sentences = text.replace('\n', ' ').split('。')
    sentences = [s.strip() + '。' for s in sentences if s.strip()]

    chunks = []
    current_chunk = ""
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        if current_length + sentence_length < chunk_size:
            current_chunk += sentence
            current_length += sentence_length
        else:
            if current_chunk:
                chunks.append(current_chunk)

            # 添加overlap
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + sentence
                current_length = overlap + sentence_length
            else:
                current_chunk = sentence
                current_length = sentence_length

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# 测试代码
if __name__ == "__main__":
    db = VectorDatabase()

    # 测试文本
    texts = [
        "Transformer模型是一种基于注意力机制的深度学习架构。",
        "BERT使用双向Transformer编码器进行预训练。",
        "GPT采用自回归语言模型进行文本生成。"
    ]

    # 添加文本
    db.add(texts)

    # 检索
    results = db.search("什么是Transformer?", top_k=2)

    print("\n检索结果:")
    for i, result in enumerate(results):
        print(f"\n结果{i+1}:")
        print(f"文本: {result['text']}")
        print(f"分数: {result['score']:.4f}")

    # 保存
    db.save()
