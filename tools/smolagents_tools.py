"""
基于 smolagents 的工具集
"""
from smolagents import tool
from pathlib import Path
import json
from typing import List, Dict
from magic_pdf.pipe.UNIPipe import UNIPipe
import numpy as np
import faiss
import pickle
from openai import OpenAI
import os

# ============================================================================
# Tool 1: PDF解析工具 (使用 MinerU)
# ============================================================================

@tool
def parse_pdf(pdf_path: str) -> str:
    """
    Parse a PDF file and extract text, images, tables, and formulas using MinerU.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        JSON string containing extracted content
    """
    try:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return json.dumps({"error": f"File not found: {pdf_path}"})

        # 读取PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # 创建输出目录
        output_dir = Path("./data/processed") / pdf_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        # 使用MinerU解析
        pipe = UNIPipe(pdf_bytes, {"_pdf_type": ""}, "auto")
        pipe.pipe_classify()
        pipe.pipe_analyze()
        pipe.pipe_parse()

        content_list = pipe.pipe_mk_uni_format(str(pdf_path), str(output_dir))

        # 整理结果
        result = {
            "text": "",
            "images": [],
            "tables": [],
            "formulas": []
        }

        if isinstance(content_list, list):
            for content in content_list:
                if isinstance(content, dict):
                    content_type = content.get("type", "")
                    if content_type == "text":
                        result["text"] += content.get("text", "") + "\n"
                    elif content_type == "image":
                        result["images"].append(content.get("path", ""))
                    elif content_type == "table":
                        result["tables"].append(content.get("html", ""))
                    elif content_type == "formula":
                        result["formulas"].append(content.get("latex", ""))

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# Tool 2: 文本向量化和索引工具
# ============================================================================

class VectorStore:
    """向量存储单例"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.client = OpenAI(
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            self.dimension = 1536
            self.index = faiss.IndexFlatL2(self.dimension)
            self.texts = []
            self.index_path = Path("./data/vector_index")
            self.index_path.mkdir(parents=True, exist_ok=True)

            # 尝试加载已有索引
            if (self.index_path / "faiss.index").exists():
                self.load()

            VectorStore._initialized = True

    def embed(self, text: str) -> np.ndarray:
        """文本向量化"""
        response = self.client.embeddings.create(
            model="text-embedding-v3",
            input=text
        )
        return np.array(response.data[0].embedding, dtype='float32')

    def add_texts(self, texts: List[str]):
        """添加文本"""
        embeddings = []
        for text in texts:
            emb = self.embed(text)
            embeddings.append(emb)

        embeddings = np.array(embeddings).astype('float32')
        self.index.add(embeddings)
        self.texts.extend(texts)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索"""
        if self.index.ntotal == 0:
            return []

        query_emb = self.embed(query).reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_emb, min(top_k, self.index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.texts):
                results.append({
                    "text": self.texts[idx],
                    "score": float(distances[0][i])
                })
        return results

    def save(self):
        """保存索引"""
        faiss.write_index(self.index, str(self.index_path / "faiss.index"))
        with open(self.index_path / "texts.pkl", 'wb') as f:
            pickle.dump(self.texts, f)

    def load(self):
        """加载索引"""
        self.index = faiss.read_index(str(self.index_path / "faiss.index"))
        with open(self.index_path / "texts.pkl", 'rb') as f:
            self.texts = pickle.load(f)

# 全局向量存储实例
vector_store = VectorStore()


@tool
def index_text(text: str, chunk_size: int = 500) -> str:
    """
    Index text into vector database after chunking.

    Args:
        text: Text to index
        chunk_size: Size of each chunk

    Returns:
        Status message
    """
    try:
        # 分块
        sentences = text.replace('\n', ' ').split('。')
        sentences = [s.strip() + '。' for s in sentences if s.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        # 索引
        vector_store.add_texts(chunks)
        vector_store.save()

        return f"Successfully indexed {len(chunks)} chunks"

    except Exception as e:
        return f"Error indexing text: {str(e)}"


@tool
def search_knowledge(query: str, top_k: int = 5) -> str:
    """
    Search for relevant information from indexed documents.

    Args:
        query: Search query
        top_k: Number of results to return

    Returns:
        JSON string of search results
    """
    try:
        results = vector_store.search(query, top_k)
        return json.dumps(results, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# Tool 3: 图像理解工具 (使用 Qwen-VL)
# ============================================================================

@tool
def understand_image(image_path: str, question: str = "请详细描述这张图表") -> str:
    """
    Understand and describe an image using Qwen-VL model.

    Args:
        image_path: Path to the image file
        question: Question about the image

    Returns:
        Description of the image
    """
    try:
        import base64

        image_path = Path(image_path)
        if not image_path.exists():
            return f"Image not found: {image_path}"

        # 读取图像
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # 调用Qwen-VL API
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        response = client.chat.completions.create(
            model="qwen-vl-max",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error understanding image: {str(e)}"


# ============================================================================
# Tool 4: 综合工具 - 处理整个PDF并索引
# ============================================================================

@tool
def process_and_index_pdf(pdf_path: str) -> str:
    """
    Process a PDF file with MinerU and index the content.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Processing summary
    """
    # 1. 解析PDF
    parse_result = parse_pdf(pdf_path)
    result_dict = json.loads(parse_result)

    if "error" in result_dict:
        return parse_result

    # 2. 索引文本
    text = result_dict.get("text", "")
    if text:
        index_status = index_text(text)
    else:
        index_status = "No text to index"

    # 3. 返回摘要
    summary = {
        "text_length": len(text),
        "images_count": len(result_dict.get("images", [])),
        "tables_count": len(result_dict.get("tables", [])),
        "formulas_count": len(result_dict.get("formulas", [])),
        "index_status": index_status,
        "images": result_dict.get("images", [])
    }

    return json.dumps(summary, ensure_ascii=False, indent=2)


# 导出所有工具
__all__ = [
    'parse_pdf',
    'index_text',
    'search_knowledge',
    'understand_image',
    'process_and_index_pdf'
]
