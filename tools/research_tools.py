"""
SciResearcher Tools - 基于 smolagents 的工具集
使用模块化服务架构,代码解耦,可读性高
"""
from smolagents import tool
import json
from pathlib import Path

# 导入服务模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from services import (
    PDFService,
    EmbeddingService,
    VectorStore
)
from services.vision_service import VisionService

# ============================================================================
# 全局服务实例初始化
# ============================================================================

# PDF 解析服务
pdf_service = PDFService()

# Qwen3 Embedding 服务
embedding_service = EmbeddingService(
    model_name="text-embedding-v3",
    dimension=1536
)

# 向量存储服务
vector_service = VectorStore(embedding_service=embedding_service)

# Qwen-VL 视觉服务
vision_service = VisionService(model_name="qwen-vl-max")

# ============================================================================
# smolagents 工具函数层 (简洁的委托包装)
# ============================================================================

@tool
def parse_pdf_with_mineru(pdf_url: str, model_version: str = "vlm") -> str:
    """
    Parse PDF using MinerU Cloud API.

    Args:
        pdf_url: Public PDF URL
        model_version: 'vlm' or 'pipeline'

    Returns:
        JSON with markdown, content_list, tables, images
    """
    try:
        result = pdf_service.parse(pdf_url, model_version)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def index_documents(text: str, chunk_size: int = 500, source: str = "unknown") -> str:
    """
    Index text chunks using Qwen3 Embedding.

    Args:
        text: Text to index
        chunk_size: Chunk size
        source: Source identifier

    Returns:
        Status message
    """
    try:
        # 文本分块 (按句子)
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

        # 添加到向量库
        metadata = [{"source": source, "chunk_id": i} for i in range(len(chunks))]
        vector_service.add_texts(chunks, metadata)
        vector_service.save()

        return f"✅ 成功索引 {len(chunks)} 个文本块 (来源: {source})"
    except Exception as e:
        return f"❌ 索引失败: {str(e)}"


@tool
def search_documents(query: str, top_k: int = 5) -> str:
    """
    Semantic search using Qwen3 Embedding.

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        JSON search results
    """
    try:
        results = vector_service.search(query, top_k)
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def analyze_image(image_path: str, question: str = "请详细描述这张图表的内容") -> str:
    """
    Analyze image using Qwen-VL.

    Args:
        image_path: Path to image
        question: Question about image

    Returns:
        Analysis result
    """
    try:
        image_path = Path(image_path)
        if not image_path.exists():
            return f"❌ 图像不存在: {image_path}"

        return vision_service.analyze(str(image_path), question)
    except Exception as e:
        return f"❌ 分析失败: {str(e)}"


@tool
def process_research_paper(pdf_url: str) -> str:
    """
    Complete pipeline: parse PDF and index.

    Args:
        pdf_url: PDF URL

    Returns:
        Processing summary
    """
    # 解析 PDF
    parse_result_json = parse_pdf_with_mineru(pdf_url)
    parse_result = json.loads(parse_result_json)

    if "error" in parse_result:
        return parse_result_json

    # 索引文本 (使用 markdown)
    text = parse_result.get("markdown", "")

    if text:
        index_status = index_documents(text, chunk_size=500, source=pdf_url)
    else:
        index_status = "⚠️ 无文本内容"

    # 返回摘要
    summary = {
        "pdf_url": pdf_url,
        "text_length": len(text),
        "tables_count": len(parse_result.get("tables", [])),
        "images_count": len(parse_result.get("images", [])),
        "index_status": index_status
    }

    return json.dumps(summary, ensure_ascii=False, indent=2)


# 导出
__all__ = [
    'parse_pdf_with_mineru',
    'index_documents',
    'search_documents',
    'analyze_image',
    'process_research_paper',
    # 导出服务实例供 agents 使用
    'pdf_service',
    'embedding_service',
    'vector_service',
    'vision_service'
]
