#!/usr/bin/env python3
"""
SciResearcher Gradio Web 应用
支持本地PDF上传、深度文档理解和智能问答
"""
import os
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict

import gradio as gr

# 导入工具
from tools.smolagents_tools import parse_pdf, download_mineru_result
from tools.vector_db_chroma import vector_db
from openai import OpenAI


class SciResearcherApp:
    """SciResearcher Web应用"""

    def __init__(self):
        """初始化应用"""
        self.client = OpenAI(
            api_key=os.getenv("MODELSCOPE_API_KEY"),
            base_url=os.getenv("MODELSCOPE_BASE_URL")
        )
        self.current_doc_id = None

    def upload_and_process_pdf(self, file, doc_name: str = None):
        """上传并处理PDF文件"""
        if not file:
            return "请上传PDF文件", "", None

        try:
            doc_id = doc_name or f"doc_{uuid.uuid4().hex[:8]}"
            file_name = os.path.basename(file.name) if hasattr(file, 'name') else file

            # 将文件保存到临时目录
            temp_dir = Path("./data/uploads")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / file_name

            # 读取并保存文件
            if hasattr(file, 'read'):
                with open(temp_file, 'wb') as f:
                    f.write(file.read())

                yield f"📤 正在处理本地PDF文件: {file_name}", "", None

                # 直接使用本地文件路径传递给parse_pdf
                parse_result = parse_pdf("", local_file_path=str(temp_file))
                result_dict = json.loads(parse_result)

                if "error" in result_dict:
                    yield f"❌ 解析失败: {result_dict['error']}", "", None

                # 提取内容
                content = ""
                if "result" in result_dict:
                    content = result_dict["result"].get("markdown", "")

                if not content:
                    yield "❌ 未找到解析内容", "", None

                # 添加到向量数据库
                yield "🔄 正在索引文档...", "", None

                success = vector_db.add_document(
                    doc_id=doc_id,
                    content=content,
                    metadata={"source": "mineru", "file_name": file_name}
                )

                if success:
                    yield f"✅ 文档处理完成 (ID: {doc_id})\n\n文档预览:\n{content[:500]}...", content, gr.update(value=doc_id)
                else:
                    yield "❌ 文档索引失败", "", None
            else:
                file_url = file
                yield f"📥 正在处理PDF URL: {file_url}", "", None
                # URL处理逻辑已经在process_pdf_from_url中

        except Exception as e:
            return f"❌ 处理失败: {str(e)}", "", None

    def process_pdf_from_url(self, pdf_url: str, doc_name: str = ""):
        """从URL处理PDF"""
        if not pdf_url:
            return "", gr.update(value=None)

        try:
            doc_id = doc_name or f"doc_{uuid.uuid4().hex[:8]}"
            self.current_doc_id = doc_id

            # 使用MinerU解析PDF
            yield "🔄 正在解析PDF...", "", None

            parse_result = parse_pdf(pdf_url)
            result_dict = json.loads(parse_result)

            if "error" in result_dict:
                yield f"❌ 解析失败: {result_dict['error']}", "", None

            # 提取内容
            content = ""
            if "result" in result_dict:
                content = result_dict["result"].get("markdown", "")

            if not content:
                yield "❌ 未找到解析内容", "", None

            # 添加到向量数据库
            yield "🔄 正在索引文档...", "", None

            success = vector_db.add_document(
                doc_id=doc_id,
                content=content,
                metadata={"source": "mineru", "pdf_url": pdf_url}
            )

            if success:
                yield f"✅ 文档处理完成 (ID: {doc_id})\n\n文档预览:\n{content[:500]}...", content, gr.update(value=doc_id)
            else:
                yield "❌ 文档索引失败", "", None

        except Exception as e:
            yield f"❌ 处理失败: {str(e)}", "", None

    def ask_question(self, question: str, doc_id: str = None):
        """智能问答"""
        if not question:
            return "请输入问题", []

        if not vector_db.collection:
            return "向量数据库未初始化", []

        try:
            # 搜索相关文档
            search_results = vector_db.search(question, n_results=5)

            if not search_results:
                return "未找到相关内容，请先上传并处理文档", []

            # 构建上下文
            context = "\n\n".join([f"[证据{i+1}] {r['content']}" for i, r in enumerate(search_results)])

            # 使用Qwen进行问答
            prompt = f"""基于以下文档内容回答问题：

{context}

问题: {question}

要求:
1. 基于提供的文档内容回答
2. 明确标注引用来源 [证据1] [证据2]
3. 给出置信度评分 (0-1)
4. 如果文档中没有相关信息，明确说明

回答:"""

            yield "🔄 正在生成答案...", []

            response = self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            answer = response.choices[0].message.content

            # 显示引用
            citations = []
            for i, result in enumerate(search_results, 1):
                citations.append({
                    "证据": f"证据{i}",
                    "内容": result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                    "相似度": f"{result['score']:.3f}"
                })

            return answer, citations

        except Exception as e:
            return f"❌ 问答失败: {str(e)}", []

    def deep_research(self, question: str, doc_id: str = None):
        """深度研究分析"""
        if not question:
            return "请输入研究问题", []

        if not vector_db.collection:
            return "向量数据库未初始化", []

        try:
            # 搜索相关内容
            search_results = vector_db.search(question, n_results=10)
            context = "\n\n".join([f"[证据{i+1}] {r['content']}" for i, r in enumerate(search_results)])

            # 深度分析提示词
            prompt = f"""请对以下文档内容进行深度研究分析：

{context}

研究问题: {question}

请从以下角度进行深入分析:
1. 核心观点总结
2. 关键证据和论据
3. 方法论分析
4. 创新点和贡献
5. 局限性和不足
6. 未来研究方向
7. 实际应用价值

请提供详细、深入的分析，并明确标注引用来源 [证据1] [证据2]"""

            yield "🔄 正在进行深度研究分析...", []

            response = self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = response.choices[0].message.content

            return analysis, search_results

        except Exception as e:
            return f"❌ 深度研究失败: {str(e)}", []

    def get_document_list(self):
        """获取文档列表"""
        try:
            docs = vector_db.list_documents()
            if not docs:
                return "暂无文档"

            doc_list = []
            for doc in docs:
                doc_list.append(f"📄 {doc['doc_id']} ({doc['chunk_count']} 块)")

            return "\n".join(doc_list)
        except Exception as e:
            return f"获取文档列表失败: {str(e)}"

    def clear_database(self):
        """清空数据库"""
        try:
            import shutil
            if Path("./data/chromadb").exists():
                shutil.rmtree("./data/chromadb")
            return "✅ 数据库已清空", self.get_document_list()
        except Exception as e:
            return f"❌ 清空失败: {str(e)}", ""


# 创建应用实例
app = SciResearcherApp()


def create_interface():
    """创建Gradio界面"""
    # 创建蓝色主题
    blue_theme = gr.themes.Default(
        primary_hue="blue",
        secondary_hue="blue",
        neutral_hue="slate"
    )

    with gr.Blocks(title="SciResearcher - 科研文献深度理解系统", theme=blue_theme) as interface:
        gr.Markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
            <h1 style='margin: 0; font-size: 2.5em;'>🔬 SciResearcher</h1>
            <h2 style='margin: 10px 0; font-weight: normal;'>科研文献深度理解系统</h2>
            <p style='font-size: 1.1em; margin: 10px 0;'>基于 MinerU + 魔搭API + ChromaDB 的科研文献智能分析平台</p>
        </div>

        ## ✨ 核心功能

        <div style='display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0;'>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #E3F2FD; border-radius: 8px; border-left: 4px solid #2196F3;'>
                <h4 style='margin: 0 0 10px 0; color: #1976D2;'>📄 智能文档处理</h4>
                <p style='margin: 0; font-size: 0.95em;'>支持本地PDF上传和在线链接，智能解析文档内容</p>
            </div>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #E8F5E9; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                <h4 style='margin: 0 0 10px 0; color: #388E3C;'>🔍 向量检索</h4>
                <p style='margin: 0; font-size: 0.95em;'>基于ChromaDB的高效语义检索系统</p>
            </div>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #FFF3E0; border-radius: 8px; border-left: 4px solid #FF9800;'>
                <h4 style='margin: 0 0 10px 0; color: #F57C00;'>💬 智能问答</h4>
                <p style='margin: 0; font-size: 0.95em;'>基于Qwen-Plus的深度文档理解和问答</p>
            </div>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #F3E5F5; border-radius: 8px; border-left: 4px solid #9C27B0;'>
                <h4 style='margin: 0 0 10px 0; color: #7B1FA2;'>🎯 深度研究</h4>
                <p style='margin: 0; font-size: 0.95em;'>多维度文献分析，洞察科研价值</p>
            </div>
        </div>

        ## 🚀 快速开始

        <div style='background: #F5F5F5; padding: 20px; border-radius: 10px; margin: 20px 0;'>
            <h3 style='color: #1976D2; margin-top: 0;'>三步开始使用：</h3>
            <ol style='line-height: 1.8;'>
                <li><strong>上传PDF</strong> - 在"文档上传与处理"页面选择本地PDF文件或输入URL</li>
                <li><strong>智能问答</strong> - 在"智能问答"页面提问，快速获取文档相关答案</li>
                <li><strong>深度研究</strong> - 在"深度研究"页面进行深入分析和洞察</li>
            </ol>
        </div>

        ## 📊 示例结果

        <div style='background: linear-gradient(to right, #E3F2FD, #E1F5FE); padding: 20px; border-radius: 10px; margin: 20px 0;'>
            <h3 style='color: #1976D2; margin-top: 0;'>📝 智能问答示例</h3>
            <div style='background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #2196F3;'>
                <p style='margin: 0; font-style: italic; color: #555;'>❓ 问题：这篇论文的主要贡献是什么？</p>
            </div>
            <div style='background: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #4CAF50;'>
                <p style='margin: 0;'><strong>💡 回答：</strong>本文提出了一种基于Transformer的创新方法，通过改进注意力机制和引入多尺度特征融合，显著提升了模型在NLP任务上的性能。实验表明，该方法在多个基准数据集上取得了SOTA结果。</p>
                <p style='margin: 10px 0 0 0; font-size: 0.9em; color: #666;'>
                    <strong>引用来源：</strong>[证据1] 摘要部分 - 相似度: 0.95<br>
                    [证据2] 第3.2节 - 相似度: 0.92
                </p>
            </div>
        </div>

        <div style='background: linear-gradient(to right, #FFF3E0, #FFE0B2); padding: 20px; border-radius: 10px; margin: 20px 0;'>
            <h3 style='color: #F57C00; margin-top: 0;'>🎯 深度研究示例</h3>
            <div style='background: white; padding: 15px; border-radius: 8px; margin: 10px 0;'>
                <h4 style='color: #F57C00; margin: 0 0 10px 0;'>核心观点总结</h4>
                <p style='margin: 0;'>论文聚焦于解决传统NLP模型在长文本处理中的效率问题，提出了创新的解决方案。</p>

                <h4 style='color: #F57C00; margin: 15px 0 10px 0;'>创新点</h4>
                <ul style='margin: 0; line-height: 1.8;'>
                    <li>设计了自适应注意力机制，降低计算复杂度</li>
                    <li>引入分层编码策略，提升长文本理解能力</li>
                    <li>提出新的训练策略，加速模型收敛</li>
                </ul>

                <h4 style='color: #F57C00; margin: 15px 0 10px 0;'>应用价值</h4>
                <p style='margin: 0;'>该方法在文档问答、摘要生成等实际应用中展现了优异性能，为大规模文本处理提供了新思路。</p>
            </div>
        </div>
        """)

        with gr.Tab("📄 文档上传与处理"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📤 方式一：本地文件上传")
                    gr.Markdown("支持直接上传本地PDF文件，无需上传到云端", elem_id="upload-hint")
                    pdf_file = gr.File(
                        label="选择PDF文件",
                        file_types=[".pdf"]
                    )
                    doc_name = gr.Textbox(
                        label="文档名称",
                        placeholder="可选，用于标识文档"
                    )
                    upload_btn = gr.Button("🚀 开始处理", variant="primary", size="lg")

                    gr.Markdown("<br>")  # 分隔线
                    gr.Markdown("### 🔗 方式二：URL链接上传")
                    gr.Markdown("支持MinerU官方API解析", elem_id="url-hint")
                    pdf_url = gr.Textbox(
                        label="PDF文件URL",
                        placeholder="请输入PDF的直接下载链接（需要先上传到Google Drive、Dropbox等）"
                    )
                    url_btn = gr.Button("📥 从URL处理", variant="secondary", size="lg")

                with gr.Column():
                    status = gr.Textbox(
                        label="处理状态",
                        lines=5,
                        max_lines=10
                    )
                    content_preview = gr.Textbox(
                        label="内容预览",
                        lines=15,
                        max_lines=20
                    )
                    current_doc_id = gr.Textbox(
                        label="当前文档ID",
                        info="用于问答和分析"
                    )

            # 本地文件上传处理
            upload_btn.click(
                fn=app.upload_and_process_pdf,
                inputs=[pdf_file, doc_name],
                outputs=[status, content_preview, current_doc_id]
            )

            # URL上传处理
            url_btn.click(
                fn=app.process_pdf_from_url,
                inputs=[pdf_url, doc_name],
                outputs=[status, content_preview, current_doc_id]
            )

        with gr.Tab("💬 智能问答"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 💡 智能问答")
                    gr.Markdown("基于文档内容的智能问答系统，支持上下文引用和相似度评分", elem_id="qa-hint")
                    question = gr.Textbox(
                        label="您的问题",
                        placeholder="例如：这篇论文的主要贡献是什么？研究方法有哪些创新点？",
                        lines=3
                    )
                    doc_id_input = gr.Textbox(
                        label="文档ID",
                        placeholder="可选，指定特定文档进行分析"
                    )
                    ask_btn = gr.Button("🤔 开始问答", variant="primary", size="lg")

                with gr.Column():
                    answer = gr.Textbox(
                        label="答案",
                        lines=12,
                        max_lines=15
                    )
                    citations = gr.Dataframe(
                        headers=["证据", "内容", "相似度"],
                        label="引用来源"
                    )

            ask_btn.click(
                fn=app.ask_question,
                inputs=[question, doc_id_input],
                outputs=[answer, citations]
            )

        with gr.Tab("🎯 深度研究"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🔬 深度研究分析")
                    gr.Markdown("多维度文献分析，包括核心观点、方法论、创新点、局限性等", elem_id="research-hint")
                    research_question = gr.Textbox(
                        label="研究问题",
                        placeholder="例如：分析这篇论文的方法论和创新点；评估该研究的实际应用价值；探讨研究的局限性和未来方向",
                        lines=3
                    )
                    research_doc_id = gr.Textbox(
                        label="文档ID",
                        placeholder="可选"
                    )
                    research_btn = gr.Button("🔬 开始深度研究", variant="primary", size="lg")

                with gr.Column():
                    analysis = gr.Textbox(
                        label="深度分析报告",
                        lines=15,
                        max_lines=20
                    )

            research_btn.click(
                fn=app.deep_research,
                inputs=[research_question, research_doc_id],
                outputs=[analysis]
            )

        with gr.Tab("📚 文档管理"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📋 当前文档")
                    gr.Markdown("查看和管理已处理的文档", elem_id="docs-hint")
                    doc_list = gr.Textbox(
                        label="文档列表",
                        lines=10,
                        max_lines=15
                    )
                    with gr.Row():
                        refresh_btn = gr.Button("🔄 刷新列表", variant="primary")
                        clear_btn = gr.Button("🗑️ 清空数据库", variant="stop")

                with gr.Column():
                    stats = gr.Textbox(
                        label="数据库统计",
                        lines=10,
                        max_lines=15
                    )

            refresh_btn.click(
                fn=app.get_document_list,
                outputs=[doc_list]
            )

            clear_btn.click(
                fn=app.clear_database,
                outputs=[stats, doc_list]
            )

        with gr.Tab("ℹ️ 使用说明"):
            gr.Markdown("""
            ### 📖 使用指南

            #### 1️⃣ 上传PDF
            - 将PDF文件上传到Google Drive、Dropbox等文件分享服务
            - 获取直接下载链接（.pdf结尾的URL）
            - 在"文档上传与处理"标签页中输入URL并点击"开始处理"

            #### 2️⃣ 智能问答
            - 在"智能问答"标签页中输入您的问题
            - 系统会自动搜索相关文档片段并生成答案
- 答案会标注引用来源和置信度

            #### 3️⃣ 深度研究
            - 在"深度研究"标签页中进行深入分析
            - 系统会从多个维度分析文档内容
            - 包括观点总结、论据分析、方法论等

            #### 4️⃣ 文档管理
            - 查看已处理的文档列表
            - 清空数据库（会删除所有索引）

            ### 🔧 技术架构
            - **PDF解析**: MinerU 官方API
            - **向量检索**: ChromaDB + 魔搭Embedding
            - **问答引擎**: 魔搭 Qwen-Plus
            - **Web界面**: Gradio

            ### ⚠️ 注意事项
            - PDF URL必须是公开可访问的直接下载链接
            - 首次处理可能需要几分钟时间
            - 文档会持久化存储在 ./data/ 目录
            """)

    return interface


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )
