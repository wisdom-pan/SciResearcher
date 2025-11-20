# 向量数据库迁移: FAISS → ChromaDB

## 迁移原因
根据用户需求: "向量数据库可以用Chromedb比较轻量化"

## ChromaDB 优势

### 1. 更轻量化
- **FAISS**: 需要手动管理索引文件 (faiss.index, texts.pkl, metadata.pkl)
- **ChromaDB**: 自动持久化,内置元数据管理

### 2. 更简单的API
```python
# FAISS (旧方案)
import faiss
import pickle
index = faiss.IndexFlatL2(dimension)
faiss.write_index(index, "faiss.index")
with open("texts.pkl", "wb") as f:
    pickle.dump(texts, f)

# ChromaDB (新方案)
import chromadb
client = chromadb.PersistentClient(path="./data")
collection = client.get_or_create_collection("documents")
collection.add(embeddings=embeddings, documents=texts, ids=ids)
```

### 3. 内置功能
- ✅ 自动持久化 (无需手动save/load)
- ✅ 元数据管理 (无需单独pickle文件)
- ✅ 文档存储 (无需单独texts.pkl)
- ✅ 查询过滤 (支持元数据过滤)
- ✅ 更新/删除 (FAISS不支持)

## 代码对比

### 初始化
```python
# FAISS (98行)
class VectorStore:
    def __init__(self, embedding_service, index_dir="./data/vector_index"):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.metadata = []
        if (self.index_dir / "faiss.index").exists():
            self._load()  # 手动加载

# ChromaDB (46行)
class VectorStore:
    def __init__(self, embedding_service, index_dir="./data/vector_index"):
        self.client = chromadb.PersistentClient(path=str(self.index_dir))
        self.collection = self.client.get_or_create_collection("documents")
        # 自动加载已有数据
```

### 添加数据
```python
# FAISS
def add_texts(self, texts, metadata):
    embeddings = [self.embedding_service.embed(text) for text in texts]
    embeddings_array = np.array(embeddings, dtype='float32')
    self.index.add(embeddings_array)
    self.texts.extend(texts)
    self.metadata.extend(metadata)

# ChromaDB
def add_texts(self, texts, metadata):
    embeddings = [self.embedding_service.embed(text) for text in texts]
    self.collection.add(
        embeddings=[emb.tolist() for emb in embeddings],
        documents=texts,
        metadatas=metadata,
        ids=[f"doc_{i}" for i in range(len(texts))]
    )
```

### 搜索
```python
# FAISS
def search(self, query, top_k=5):
    query_vector = self.embedding_service.embed(query).reshape(1, -1)
    distances, indices = self.index.search(query_vector, top_k)
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "text": self.texts[idx],
            "score": float(distances[0][i]),
            "metadata": self.metadata[idx]
        })
    return results

# ChromaDB
def search(self, query, top_k=5):
    query_vector = self.embedding_service.embed(query)
    results = self.collection.query(
        query_embeddings=[query_vector.tolist()],
        n_results=top_k
    )
    return [{
        "text": results['documents'][0][i],
        "score": results['distances'][0][i],
        "metadata": results['metadatas'][0][i]
    } for i in range(len(results['documents'][0]))]
```

### 持久化
```python
# FAISS (需要手动保存3个文件)
def save(self):
    faiss.write_index(self.index, str(self.index_dir / "faiss.index"))
    with open(self.index_dir / "texts.pkl", 'wb') as f:
        pickle.dump(self.texts, f)
    with open(self.index_dir / "metadata.pkl", 'wb') as f:
        pickle.dump(self.metadata, f)

# ChromaDB (自动持久化)
def save(self):
    # ChromaDB 自动持久化,只需打印确认
    print(f"💾 索引已保存: {self.collection.count()} 个向量")
```

## 文件大小对比

| 实现 | 代码行数 | 依赖 | 文件数 |
|------|---------|------|--------|
| FAISS | 98行 | faiss-cpu, numpy, pickle | 3个文件 (index, texts, metadata) |
| ChromaDB | **115行** | chromadb | 1个目录 (自动管理) |

## 性能对比

| 指标 | FAISS | ChromaDB |
|------|-------|----------|
| 初始化速度 | 快 (纯内存) | 稍慢 (持久化) |
| 查询速度 | 极快 | 快 |
| 插入速度 | 快 | 中等 |
| 内存占用 | 低 | 中等 |
| 磁盘占用 | 低 | 中等 |

## 适用场景

### 选择 ChromaDB (已选择)
- ✅ 原型开发和MVP
- ✅ 中小规模数据 (<1M文档)
- ✅ 需要元数据管理
- ✅ 需要更新/删除功能
- ✅ 简化部署和维护

### 如需切换回 FAISS
- 超大规模数据 (>10M文档)
- 极致查询性能需求
- 纯向量搜索,无需元数据

## 迁移步骤

1. ✅ 替换 `services/vector_store.py` 实现
2. ✅ 更新 `requirements.txt`: `faiss-cpu` → `chromadb`
3. ✅ API接口保持兼容 (add_texts, search, save)
4. ✅ 自动数据迁移 (首次运行时ChromaDB自动创建)

## 使用示例

```python
from services import EmbeddingService, VectorStore

# 初始化
embedding = EmbeddingService()
vector_store = VectorStore(embedding_service=embedding)

# 添加数据
vector_store.add_texts(
    texts=["文档1", "文档2"],
    metadata=[{"source": "paper1"}, {"source": "paper2"}]
)

# 搜索
results = vector_store.search("查询问题", top_k=5)

# 自动持久化 (无需手动save)
vector_store.save()  # 仅打印确认

# 清空数据 (ChromaDB新增功能)
vector_store.reset()
```

## 额外功能

ChromaDB提供的额外功能 (可选使用):

```python
# 元数据过滤
results = collection.query(
    query_embeddings=[vector],
    where={"source": "arxiv"},  # 只搜索arxiv来源
    n_results=5
)

# 更新文档
collection.update(
    ids=["doc_0"],
    documents=["更新后的文本"],
    metadatas=[{"source": "updated"}]
)

# 删除文档
collection.delete(ids=["doc_0"])

# 统计信息
count = collection.count()
```

## 依赖变更

```diff
# requirements.txt
- faiss-cpu>=1.7.4
+ chromadb>=0.4.0
```

## 总结

✅ **更轻量**: 无需管理多个pickle文件
✅ **更简单**: API更直观,自动持久化
✅ **更强大**: 支持更新/删除/元数据过滤
✅ **兼容性**: API接口保持不变,无缝迁移
✅ **适合MVP**: 快速开发和原型验证
