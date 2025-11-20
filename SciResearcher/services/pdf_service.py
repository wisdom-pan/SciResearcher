"""
MinerU PDF 解析服务
"""
import os
import time
import requests
import zipfile
import io
import json
from typing import Dict, Any

class PDFService:
    """MinerU 云服务 PDF 解析"""

    def __init__(self, api_token: str = None, timeout: int = 300):
        self.api_token = api_token or os.getenv("MINERU_API_TOKEN", "")
        self.timeout = timeout
        self.base_url = "https://mineru.net/api/v4"

    def parse(self, pdf_url: str, model_version: str = "vlm") -> Dict[str, Any]:
        """解析 PDF"""
        print(f"📤 提交 PDF: {pdf_url[:60]}...")

        task_id = self._submit_task(pdf_url, model_version)
        print(f"✅ 任务 ID: {task_id}")

        result = self._poll_task(task_id)
        print(f"📥 下载结果...")

        return self._extract_zip(result["full_zip_url"])

    def _submit_task(self, pdf_url: str, model_version: str) -> str:
        """提交任务"""
        url = f"{self.base_url}/extract/task"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        data = {"url": pdf_url, "model_version": model_version}

        res = requests.post(url, headers=headers, json=data, timeout=10)
        res.raise_for_status()
        resp = res.json()

        if resp["code"] != 0:
            raise RuntimeError(f"任务提交失败: {resp['msg']}")

        return resp["data"]["task_id"]

    def _poll_task(self, task_id: str, interval: int = 5) -> Dict[str, Any]:
        """轮询任务"""
        url = f"{self.base_url}/extract/task/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        start = time.time()

        while time.time() - start < self.timeout:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            resp = res.json()

            if resp["code"] != 0:
                raise RuntimeError(f"轮询失败: {resp['msg']}")

            data = resp["data"]
            state = data["state"]

            if state == "done":
                return data
            elif state == "failed":
                raise RuntimeError(f"解析失败: {data.get('err_msg', '未知错误')}")
            elif state == "running":
                progress = data["extract_progress"]
                print(f"📄 进度: {progress['extracted_pages']}/{progress['total_pages']} 页")

            time.sleep(interval)

        raise TimeoutError("解析超时")

    def _extract_zip(self, zip_url: str) -> Dict[str, Any]:
        """提取 ZIP 内容"""
        res = requests.get(zip_url, timeout=60)
        res.raise_for_status()

        result = {"markdown": "", "content_list": [], "tables": [], "images": []}

        with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
            # Markdown
            try:
                result["markdown"] = zf.read("output.md").decode("utf-8")
            except KeyError:
                pass

            # Content List
            try:
                result["content_list"] = json.loads(zf.read("content_list.json"))
            except KeyError:
                pass

            # Tables
            try:
                from bs4 import BeautifulSoup
                tables_html = zf.read("tables.html").decode("utf-8")
                soup = BeautifulSoup(tables_html, "html.parser")

                for tbl in soup.find_all("table"):
                    caption = tbl.find_previous("p", string=lambda x: x and "Table" in x)
                    result["tables"].append({
                        "html": str(tbl),
                        "caption": caption.get_text() if caption else ""
                    })
            except Exception:
                pass

            # Images
            try:
                result["images"] = [
                    {"path_in_zip": name}
                    for name in zf.namelist()
                    if name.startswith("images/") and name.endswith(".jpg")
                ]
            except Exception:
                pass

        return result
