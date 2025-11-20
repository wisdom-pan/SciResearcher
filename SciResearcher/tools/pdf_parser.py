"""
PDF解析工具 - 使用MinerU
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Any
from magic_pdf.pipe.UNIPipe import UNIPipe

class PDFParser:
    """PDF解析器，使用MinerU提取文字、图片、公式、表格"""

    def __init__(self, output_dir: str = "./data/processed"):
        """初始化PDF解析器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """解析PDF文件

        Args:
            pdf_path: PDF文件路径

        Returns:
            dict: {
                "text": "提取的文字",
                "images": ["图片1路径", "图片2路径"],
                "tables": ["表格1 HTML", "表格2 HTML"],
                "formulas": ["公式1 LaTeX", "公式2 LaTeX"],
                "metadata": {...}
            }
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 读取PDF字节
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # 创建输出目录
        output_subdir = self.output_dir / pdf_path.stem
        output_subdir.mkdir(parents=True, exist_ok=True)

        # 初始化MinerU
        try:
            pipe = UNIPipe(pdf_bytes, {"_pdf_type": ""}, "auto")

            # 执行解析
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()

            # 获取结果
            content_list = pipe.pipe_mk_uni_format(
                str(pdf_path),
                str(output_subdir)
            )

            # 整理结果
            result = {
                "text": "",
                "images": [],
                "tables": [],
                "formulas": [],
                "metadata": {
                    "filename": pdf_path.name,
                    "pages": len(content_list) if isinstance(content_list, list) else 0
                }
            }

            # 解析内容
            if isinstance(content_list, list):
                for content in content_list:
                    if isinstance(content, dict):
                        content_type = content.get("type", "")

                        if content_type == "text":
                            result["text"] += content.get("text", "") + "\n"
                        elif content_type == "image":
                            image_path = content.get("path", "")
                            if image_path:
                                result["images"].append(image_path)
                        elif content_type == "table":
                            table_html = content.get("html", "")
                            if table_html:
                                result["tables"].append(table_html)
                        elif content_type == "formula":
                            formula_latex = content.get("latex", "")
                            if formula_latex:
                                result["formulas"].append(formula_latex)

            # 保存结果到JSON
            result_file = output_subdir / "parsed_result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            return result

        except Exception as e:
            # 如果MinerU失败，使用备用方案
            print(f"MinerU解析失败: {e}, 使用备用方案")
            return self._fallback_parse(pdf_path)

    def _fallback_parse(self, pdf_path: Path) -> Dict[str, Any]:
        """备用PDF解析方案 - 使用pdfplumber

        Args:
            pdf_path: PDF文件路径

        Returns:
            解析结果
        """
        try:
            import pdfplumber

            result = {
                "text": "",
                "images": [],
                "tables": [],
                "formulas": [],
                "metadata": {
                    "filename": pdf_path.name,
                    "fallback": True
                }
            }

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # 提取文字
                    text = page.extract_text()
                    if text:
                        result["text"] += text + "\n"

                    # 提取表格
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            # 转换为HTML
                            html = self._table_to_html(table)
                            result["tables"].append(html)

            return result

        except Exception as e:
            print(f"备用解析也失败: {e}")
            return {
                "text": "",
                "images": [],
                "tables": [],
                "formulas": [],
                "metadata": {
                    "filename": pdf_path.name,
                    "error": str(e)
                }
            }

    def _table_to_html(self, table: List[List[str]]) -> str:
        """将表格转换为HTML

        Args:
            table: 表格数据

        Returns:
            HTML字符串
        """
        html = "<table border='1'>\n"

        for i, row in enumerate(table):
            html += "  <tr>\n"
            tag = "th" if i == 0 else "td"

            for cell in row:
                cell_text = cell if cell else ""
                html += f"    <{tag}>{cell_text}</{tag}>\n"

            html += "  </tr>\n"

        html += "</table>"
        return html

# 测试代码
if __name__ == "__main__":
    parser = PDFParser()
    result = parser.parse("./data/pdfs/sample_paper.pdf")

    print(f"提取文字长度: {len(result['text'])}")
    print(f"图片数量: {len(result['images'])}")
    print(f"表格数量: {len(result['tables'])}")
    print(f"公式数量: {len(result['formulas'])}")
