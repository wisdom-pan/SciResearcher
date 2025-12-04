"""
基于 smolagents 的工具集
完全使用API实现，无本地依赖
"""
from smolagents import tool
from pathlib import Path
import json
import requests
import zipfile
import io
import time
from typing import List, Dict
from openai import OpenAI
import os

# ============================================================================
# MinerU API 封装函数
# ============================================================================

def create_task(file_url: str, file_path: str = None) -> str:
    """
    创建MinerU解析任务
    支持URL和本地文件上传
    """
    token = os.getenv("MINERU_API_TOKEN")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # 如果提供了本地文件路径，则使用临时URL上传方式
    if file_path and os.path.exists(file_path):
        pdf_filename = os.path.basename(file_path)
        print(f"📤 正在申请临时上传URL: {pdf_filename}")

        # 1. 申请批量上传URL
        apply_url = "https://mineru.net/api/v4/file-urls/batch"
        request_data = {
            "files": [{"name": pdf_filename}],
            "model_version": "vlm"
        }

        try:
            apply_res = requests.post(apply_url, headers=headers, json=request_data)
            apply_res.raise_for_status()
            apply_data = apply_res.json()

            if apply_data["code"] != 0:
                raise RuntimeError(f"申请上传URL失败: {apply_data['msg']}")

            batch_id = apply_data["data"]["batch_id"]
            upload_url = apply_data["data"]["file_urls"][0]
            print(f"✅ 申请临时上传URL成功，batch_id: {batch_id}")
        except Exception as e:
            raise RuntimeError(f"申请上传URL异常: {str(e)}")

        # 2. PUT方式上传文件到OSS（核心：绕过网关payload限制）
        try:
            print(f"📤 正在通过PUT方式上传文件...")
            with open(file_path, "rb") as f:
                upload_res = requests.put(upload_url, data=f)

            if upload_res.status_code not in (200, 201):
                raise RuntimeError(f"文件上传失败：状态码{upload_res.status_code}")

            print(f"✅ PDF文件上传成功（PUT方式）")
        except Exception as e:
            raise RuntimeError(f"文件上传异常: {str(e)}")

        # 3. 返回batch_id作为task_id
        return batch_id

    # 如果使用的是URL，则使用原来的URL解析方式
    else:
        url = 'https://mineru.net/api/v4/extract/task'
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        data = {
            'url': file_url,
            'is_ocr': True,
            'enable_formula': True,
            'enable_table': True,
            'language': "ch",
            'model_version': "v2"
        }
        res = requests.post(url, headers=header, json=data, timeout=30)

        res.raise_for_status()
        res_data = res.json()

        if res_data["code"] != 0:
            raise RuntimeError(f"任务提交失败: {res_data['msg']}")

        task_id_data = res_data["data"]["task_id"]
        return task_id_data


def query_by_id(task_id: str, max_retries: int = 60, retry_interval: int = 10) -> str:
    """
    优化后的轮询查询解析结果（先判断状态，再处理full_zip_url）
    支持批量结果查询和详细状态反馈
    """
    # 使用批量结果查询端点
    url = f'https://mineru.net/api/v4/extract-results/batch/{task_id}'
    token = os.getenv("MINERU_API_TOKEN")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    retries = 0
    while retries < max_retries:
        try:
            res = requests.get(url, headers=headers, timeout=30)
            res.raise_for_status()  # 捕获HTTP请求错误
            data = res.json()

            if data["code"] != 0:
                print(f"❌ 查询解析状态失败：{data['msg']}")
                break

            # 核心：先获取任务状态，再判断是否读取full_zip_url
            extract_result = data["data"]["extract_result"]
            if not extract_result:
                print(f"❌ 第{retries+1}次查询：extract_result为空")
                time.sleep(retry_interval)
                retries += 1
                continue

            task_info = extract_result[0]
            task_state = task_info["state"]
            task_err_msg = task_info.get("err_msg", "")

            # 状态分类处理
            if task_state == "done":
                # 任务完成，检查full_zip_url是否有效
                full_zip_url = task_info.get("full_zip_url", "")
                if full_zip_url:
                    print(f"✅ 任务完成！获取到结果URL")
                    return full_zip_url
                else:
                    print(f"⚠️ 任务状态为done，但full_zip_url为空，重试第{retries+1}次...")

            elif task_state == "failed":
                print(f"❌ 解析任务失败：{task_err_msg}")
                raise Exception(f"解析任务失败：{task_err_msg}")

            else:
                # 任务处理中（pending/running/converting）
                print(f"⏳ 解析中（状态：{task_state}），full_zip_url暂未生成，等待{retry_interval}秒... 已重试{retries+1}次")

            # 未完成则等待重试
            time.sleep(retry_interval)
            retries += 1

        except requests.exceptions.RequestException as e:
            print(f"❌ 查询解析结果异常：{str(e)}，重试第{retries+1}次...")
            time.sleep(retry_interval)
            retries += 1

    # 最终结果判断
    raise Exception(f"解析超时（超过{max_retries*retry_interval/60}分钟），请检查任务状态或联系MinerU官方")


def download_and_extract_zip(zip_url: str) -> Dict[str, any]:
    """
    下载并提取ZIP文件内容
    优先使用full.md作为最终解析文件
    """
    print(f"📥 Downloading: {zip_url[:60]}...")
    res = requests.get(zip_url, timeout=300)
    res.raise_for_status()

    result = {"markdown": "", "content_list": [], "tables": [], "images": []}

    with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
        # 核心：优先查找full.md（MinerU默认的完整解析结果文件）
        md_file_found = False
        for md_filename in ["full.md", "output.md", "parsed.md", "document.md"]:
            try:
                markdown_content = zf.read(md_filename).decode("utf-8")
                result["markdown"] = markdown_content
                print(f"✅ 成功读取解析文件: {md_filename}")
                md_file_found = True
                break
            except KeyError:
                continue

        if not md_file_found:
            print("⚠️ 未找到标准MD文件，列出压缩包内容以便排查:")
            for name in zf.namelist():
                print(f"  - {name}")

        # Content List
        try:
            result["content_list"] = json.loads(zf.read("content_list.json"))
        except KeyError:
            pass

        # Tables
        try:
            tables_html = zf.read("tables.html").decode("utf-8")
            result["tables_html"] = tables_html
        except KeyError:
            pass

        # Images
        try:
            result["images"] = [
                {"path_in_zip": name}
                for name in zf.namelist()
                if name.startswith("images/") and (name.endswith(".jpg") or name.endswith(".png"))
            ]
        except Exception:
            pass

    # 验证markdown内容是否完整
    if result["markdown"]:
        markdown_preview = result["markdown"][:300]
        print(f"\n📝 解析内容预览:\n{markdown_preview}...")
        print(f"✅ 完整解析结果提取完成 (总长度: {len(result['markdown'])} 字符)")
    else:
        print("⚠️ 警告: 未能提取到Markdown内容")

    return result


# ============================================================================
# Tool 1: PDF解析工具 (使用 MinerU API)
# ============================================================================

@tool
def parse_pdf(pdf_url: str, local_file_path: str = None) -> str:
    """
    Parse a PDF file using MinerU API.

    Args:
        pdf_url: URL to the PDF file (used if local_file_path not provided)
        local_file_path: Path to local PDF file (preferred if provided)

    Returns:
        JSON string containing extracted content
    """
    try:
        api_token = os.getenv("MINERU_API_TOKEN")
        if not api_token:
            return json.dumps({"error": "MINERU_API_TOKEN not configured"})

        # 如果提供了本地文件路径
        if local_file_path and os.path.exists(local_file_path):
            print(f"📤 Processing local PDF: {local_file_path}")
            task_id = create_task("", file_path=local_file_path)
        elif pdf_url:
            print(f"📥 Processing PDF from URL: {pdf_url}")
            task_id = create_task(pdf_url)
        else:
            return json.dumps({"error": "请提供PDF URL或本地文件路径"})

        # 查询任务状态并获取结果
        zip_url = query_by_id(task_id)
        result = download_and_extract_zip(zip_url)

        return json.dumps({"result": result}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def download_mineru_result(zip_url: str) -> str:
    """
    Download and extract MinerU parsing results.

    Args:
        zip_url: ZIP file URL from parse_pdf result

    Returns:
        JSON string with extracted content
    """
    try:
        result = download_and_extract_zip(zip_url)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# Tool 2: 简单的文本处理和存储 (内存存储，无本地依赖)
# ============================================================================

class SimpleTextStore:
    """简单的文本存储，不使用向量数据库"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.texts = []
            self.index_path = Path("./data/text_index.json")
            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            # 尝试加载已有索引
            if self.index_path.exists():
                try:
                    with open(self.index_path, 'r') as f:
                        self.texts = json.load(f)
                except Exception:
                    self.texts = []

            SimpleTextStore._initialized = True

    def add_texts(self, texts: List[str]):
        """添加文本"""
        self.texts.extend(texts)
        self._save()

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """简单的文本搜索（基于关键词匹配）"""
        if not self.texts:
            return []

        # 简单的关键词匹配
        query_words = query.lower().split()
        results = []

        for text in self.texts:
            text_lower = text.lower()
            score = sum(1 for word in query_words if word in text_lower)
            if score > 0:
                results.append({
                    "text": text[:500] + "..." if len(text) > 500 else text,
                    "score": float(score)
                })

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _save(self):
        """保存文本"""
        with open(self.index_path, 'w') as f:
            json.dump(self.texts, f)


# 全局文本存储实例
text_store = SimpleTextStore()


@tool
def index_text(text: str, chunk_size: int = 500) -> str:
    """
    Index text by chunking and storing in memory.

    Args:
        text: Text to index
        chunk_size: Size of each chunk

    Returns:
        Status message
    """
    try:
        # 简单的分块
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

        # 存储到内存
        text_store.add_texts(chunks)

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
        results = text_store.search(query, top_k)
        return json.dumps(results, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# Tool 3: 图像理解工具 (使用 Qwen-VL API)
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

        # 调用Qwen-VL API (魔搭)
        client = OpenAI(
            api_key=os.getenv("MODELSCOPE_API_KEY"),
            base_url=os.getenv("MODELSCOPE_BASE_URL")
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
def process_and_index_pdf(pdf_url: str) -> str:
    """
    Process a PDF file with MinerU and index the content.

    Args:
        pdf_url: URL to PDF file

    Returns:
        Processing summary
    """
    try:
        # 1. 解析PDF
        print(f"📄 Starting PDF processing...")
        parse_result = parse_pdf(pdf_url)
        result_dict = json.loads(parse_result)

        if "error" in result_dict:
            return parse_result

        zip_url = result_dict.get("zip_url")
        if not zip_url:
            return json.dumps({"error": "No zip_url in result"})

        # 2. 下载结果
        print(f"📥 Downloading results...")
        download_result = download_mineru_result(zip_url)
        download_dict = json.loads(download_result)

        if "error" in download_dict:
            return download_result

        # 3. 提取文本
        markdown = download_dict.get("markdown", "")
        if not markdown:
            return json.dumps({"error": "No markdown content found"})

        print(f"📝 Indexing text...")
        index_status = index_text(markdown)

        # 4. 返回摘要
        summary = {
            "markdown_length": len(markdown),
            "images_count": len(download_dict.get("images", [])),
            "tables_count": len(download_dict.get("tables", [])),
            "index_status": index_status,
            "images": download_dict.get("images", []),
            "markdown_preview": markdown[:500] + "..." if len(markdown) > 500 else markdown
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


# 导出所有工具
__all__ = [
    'parse_pdf',
    'download_mineru_result',
    'index_text',
    'search_knowledge',
    'understand_image',
    'process_and_index_pdf'
]
