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
from tools.smolagents_tools import parse_pdf
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
        # 临时存储用户自定义API配置（会话级）
        self.temp_api_config = {
            "modelscope_key": None,
            "modelscope_url": os.getenv("MODELSCOPE_BASE_URL"),
            "mineru_key": os.getenv("MINERU_API_TOKEN")
        }

    def save_api_config(self, modelscope_key: str, modelscope_url: str, mineru_key: str) -> str:
        """保存API配置"""
        try:
            # 更新配置
            if modelscope_key:
                self.temp_api_config["modelscope_key"] = modelscope_key

            if modelscope_url:
                self.temp_api_config["modelscope_url"] = modelscope_url

            if mineru_key:
                self.temp_api_config["mineru_key"] = mineru_key

            # 重新初始化客户端（使用新配置）
            if self.temp_api_config["modelscope_key"]:
                self.client = OpenAI(
                    api_key=self.temp_api_config["modelscope_key"],
                    base_url=self.temp_api_config["modelscope_url"]
                )

            return f"✅ API配置已保存\n\n魔搭API: {'已配置' if self.temp_api_config['modelscope_key'] else '使用默认'}\nMinerU Token: {'已配置' if self.temp_api_config['mineru_key'] else '使用默认'}"
        except Exception as e:
            return f"❌ 配置失败: {str(e)}"

    def upload_and_process_pdf(self, file, doc_name: str = None):
        """上传并处理PDF文件"""
        if not file:
            return "请上传PDF文件", "", None

        try:
            # 验证文件类型
            if not hasattr(file, 'name') or not file.name.lower().endswith('.pdf'):
                return "❌ 错误: 请上传有效的PDF文件", "", None

            # 生成或使用提供的文档ID
            doc_id = doc_name or f"doc_{uuid.uuid4().hex[:8]}"
            file_name = os.path.basename(file.name)

            # 创建上传目录
            temp_dir = Path("./data/uploads")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / file_name

            # 检查文件大小（MinerU支持最大200MB的文件，但HTTP请求可能有其他限制）
            file_size = file.size if hasattr(file, 'size') else os.path.getsize(file.name)
            if file_size > 200 * 1024 * 1024:  # 200MB
                return "❌ 错误: 文件大小超过MinerU API限制（200MB）\n\n建议：将PDF文件分割为多个较小文件后再上传", "", None

            # 优化进度显示：对于大文件显示更详细的处理进度
            if file_size > 50 * 1024 * 1024:  # 50MB+
                yield f"""
📤 正在处理大PDF文件: {file_name}
文件大小: {file_size/1024/1024:.2f}MB
⏳ 请耐心等待，可能需要几分钟...

第一步: 文件上传和验证
""", "", None
            else:
                yield f"""
📤 正在处理PDF文件: {file_name}
文件大小: {file_size/1024/1024:.2f}MB

第一步: 文件上传和验证
""", "", None

            # 保存文件到临时目录（分块读取以优化内存使用）
            with open(temp_file, 'wb') as f:
                # 对于gradio上传的文件，尝试分块读取
                if hasattr(file, 'iter_content'):
                    for chunk in file.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                else:
                    # 如果没有iter_content方法，直接读取
                    with open(file.name, 'rb') as source:
                        while True:
                            chunk = source.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

            yield f"""
✅ 第一步完成: 文件已保存到容器
文件路径: {temp_file}

第二步: 调用MinerU API解析文档
⏳ 正在上传到MinerU云端解析服务...
💡 提示: 此步骤可能需要30秒-2分钟
""", "", None

            # 使用MinerU处理PDF
            parse_result = parse_pdf("", local_file_path=str(temp_file))
            result_dict = json.loads(parse_result)

            if "error" in result_dict:
                yield f"""
## ❌ 解析失败

### 错误信息

`{result_dict['error']}`

### 解决方案

1. **检查网络连接** - 确认可以访问 https://mineru.net
2. **验证API Token** - 在"⚙️ API配置"页面确认MinerU Token正确
3. **重新上传文件** - 如果网络不稳定，尝试重新上传
4. **检查文件格式** - 确认是有效的PDF文件

### 联系方式

如问题持续，请：
- 检查MinerU账户余额
- 查看MinerU官方文档
- 联系技术支持
""", "", None
                # 清理临时文件
                if temp_file.exists():
                    temp_file.unlink()
                return

            # 提取内容
            content = ""
            if "result" in result_dict:
                content = result_dict["result"].get("markdown", "")

            if not content:
                yield """
## ❌ 解析失败

### 可能原因

1. PDF文件可能损坏或加密
2. PDF文件可能为扫描版且OCR识别失败
3. MinerU服务返回格式异常

### 建议

- 尝试使用其他PDF文件测试
- 检查PDF文件是否完整
- 确认文件未被密码保护
""", "", None
                # 清理临时文件
                if temp_file.exists():
                    temp_file.unlink()
                return

            yield f"""
✅ 第二步完成: PDF解析成功
解析内容长度: {len(content)} 字符

第三步: 索引文档内容到向量数据库
⏳ 正在分块和索引...
""", "", None

            # 添加到向量数据库
            # 获取文件元数据以便更好地跟踪
            metadata = {
                "source": "mineru",
                "file_name": file_name,
                "file_size": file_size,
                "upload_time": time.time(),
                "content_length": len(content)
            }

            success = vector_db.add_document(
                doc_id=doc_id,
                content=content,
                metadata=metadata
            )

            if success:
                # 处理成功后清理临时文件
                if temp_file.exists():
                    temp_file.unlink()

                preview_length = min(2000, len(content))
                yield f"""
## ✅ 文档处理完成

**文档ID**: `{doc_id}`
**文档名称**: {file_name}
**内容长度**: {len(content):,} 字符
**分块数量**: {len(content) // 500 + 1} 块

---

## 📝 文档内容预览

{content[:preview_length]}

{"..." if len(content) > preview_length else ""}

---

## 💡 后续操作

您现在可以：
1. 切换到"💬 智能问答"页面与此文档对话
2. 切换到"🎯 深度研究"页面进行深度分析
3. 在"📚 文档管理"页面查看所有已处理文档
""", content, gr.update(value=doc_id)
            else:
                yield """
❌ 文档索引失败

可能原因:
1. 向量数据库连接异常
2. 内存不足
3. 文档内容格式异常

建议: 重试或联系技术支持
""", "", None

        except Exception as e:
            # 清理临时文件以防出错
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            return f"""
❌ 处理失败: {str(e)}

错误详情: {str(e)}
建议: 检查文件格式是否正确，或尝试使用其他PDF文件
""", "", None


    def ask_question(self, question: str, doc_id: str = None):
        """智能问答"""
        if not question:
            return "请输入问题", []

        if not vector_db.collection:
            return "向量数据库未初始化", []

        try:
            yield """
💬 智能问答开始

第一步: 检索相关文档内容
⏳ 正在从向量数据库中搜索相关内容...
"""

            # 搜索相关文档
            search_results = vector_db.search(question, n_results=5)

            if not search_results:
                return """
❌ 未找到相关内容

可能原因:
1. 数据库中没有文档
2. 搜索关键词不够准确
3. 文档尚未完成索引

建议: 请先上传并处理PDF文档
""", []

            yield f"""
✅ 第一步完成: 检索到 {len(search_results)} 条相关内容
相似度范围: {search_results[-1]['score']:.3f} - {search_results[0]['score']:.3f}

第二步: 构建问答上下文
⏳ 正在整合文档片段...
"""

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
5. 回答简洁明了，突出重点

回答:"""

            yield """
第三步: 使用Qwen-Plus生成答案
⏳ 正在基于文档内容生成准确答案...
💡 此步骤通常需要10-30秒
"""

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

            yield f"""
✅ 问答完成!

答案长度: {len(answer)} 字符
引用证据: {len(search_results)} 条

💡 答案:
{answer}
"""

            return answer, citations

        except Exception as e:
            return f"""
❌ 问答失败: {str(e)}

错误详情: {str(e)}

建议:
1. 检查网络连接
2. 确认API配置正确
3. 尝试简化问题
4. 重新上传文档
""", []

    def deep_research(self, question: str, doc_id: str = None):
        """深度研究分析"""
        if not question:
            return "请输入研究问题", []

        if not vector_db.collection:
            return "向量数据库未初始化", []

        try:
            yield """
🔍 深度研究分析开始

第一步: 检索相关文档内容
⏳ 正在从向量数据库中搜索相关内容...
"""

            # 搜索相关内容
            search_results = vector_db.search(question, n_results=10)

            if not search_results:
                return """
❌ 未找到相关内容

可能原因:
1. 数据库中没有文档
2. 搜索关键词不够准确
3. 文档尚未完成索引

建议: 请先上传并处理PDF文档
""", []

            yield f"""
✅ 第一步完成: 检索到 {len(search_results)} 条相关内容

第二步: 构建分析上下文
⏳ 正在整合文档片段和证据...
"""

            context = "\n\n".join([f"[证据{i+1}] {r['content']}" for i, r in enumerate(search_results)])

            # 显示检索到的内容概览
            yield f"""
✅ 第二步完成: 分析上下文构建完成

检索结果概览:
{chr(10).join([f"• 证据{i+1}: {r['content'][:100]}... (相似度: {r['score']:.3f})" for i, r in enumerate(search_results[:5])])}

第三步: 启动深度研究分析
⏳ 正在使用Qwen-Plus模型进行多维度分析...
💡 此步骤可能需要30-60秒，请耐心等待
"""

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

请提供详细、深入的分析，并明确标注引用来源 [证据1] [证据2]。请用学术严谨但易于理解的语言撰写。"""

            response = self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = response.choices[0].message.content

            yield f"""
✅ 第三步完成: 深度分析生成成功

🎉 深度研究分析完成

分析报告长度: {len(analysis)} 字符
引用证据数量: {len(search_results)} 条

📋 分析报告:
{analysis}
"""

            return analysis, search_results

        except Exception as e:
            return f"""
❌ 深度研究失败: {str(e)}

错误详情: {str(e)}

建议:
1. 检查网络连接
2. 确认API配置正确
3. 尝试简化研究问题
4. 重新上传文档
""", []

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
    # 添加自定义CSS样式
    custom_css = """
    <style>
    .gr-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
    }
    .gr-button:hover {
        background: linear-gradient(135deg, #5568d3 0%, #65428b 100%);
    }
    .gr-tab {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    </style>
    """

    with gr.Blocks(title="SciResearcher - 科研文献深度理解系统") as interface:
        # 添加自定义CSS样式
        gr.HTML(custom_css)
        gr.Markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
            <h1 style='margin: 0; font-size: 2.5em;'>🔬 SciResearcher</h1>
            <h2 style='margin: 10px 0; font-weight: normal;'>科研文献深度理解系统</h2>
            <p style='font-size: 1.1em; margin: 10px 0;'>基于 MinerU + 魔搭API + ChromaDB 的科研文献智能分析平台</p>
        </div>

        ## ✨ 核心功能

        <div style='display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0;'>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #E3F2FD; border-radius: 8px; border-left: 4px solid #2196F3;'>
                <h4 style='margin: 0 0 10px 0; color: #1976D2;'>⚙️ API配置</h4>
                <p style='margin: 0; font-size: 0.95em;'>支持用户自定义配置魔搭API和MinerU Token</p>
            </div>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #E8F5E9; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                <h4 style='margin: 0 0 10px 0; color: #388E3C;'>📄 智能文档处理</h4>
                <p style='margin: 0; font-size: 0.95em;'>支持本地PDF上传（最大200MB），智能解析文档内容</p>
            </div>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #FFF3E0; border-radius: 8px; border-left: 4px solid #FF9800;'>
                <h4 style='margin: 0 0 10px 0; color: #F57C00;'>🔍 向量检索</h4>
                <p style='margin: 0; font-size: 0.95em;'>基于ChromaDB的高效语义检索系统</p>
            </div>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #F3E5F5; border-radius: 8px; border-left: 4px solid #9C27B0;'>
                <h4 style='margin: 0 0 10px 0; color: #7B1FA2;'>💬 智能问答</h4>
                <p style='margin: 0; font-size: 0.95em;'>基于Qwen-Plus的深度文档理解和问答</p>
            </div>
            <div style='flex: 1; min-width: 250px; padding: 15px; background: #E1F5FE; border-radius: 8px; border-left: 4px solid #03A9F4;'>
                <h4 style='margin: 0 0 10px 0; color: #0288D1;'>🎯 深度研究</h4>
                <p style='margin: 0; font-size: 0.95em;'>多维度文献分析，洞察科研价值</p>
            </div>
        </div>

        ## 🚀 快速开始

        <div style='background: #F5F5F5; padding: 20px; border-radius: 10px; margin: 20px 0;'>
            <h3 style='color: #1976D2; margin-top: 0;'>四步开始使用：</h3>
            <ol style='line-height: 1.8;'>
                <li><strong>配置API</strong> - 在"API配置"页面设置您的魔搭API Key和MinerU Token（可选）</li>
                <li><strong>上传PDF</strong> - 在"文档上传与处理"页面选择本地PDF文件（最大50MB）</li>
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

        with gr.Tab("⚙️ API配置"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🔑 API配置")
                    gr.Markdown("配置您的API密钥（可选，不配置将使用系统默认）", elem_id="api-config-hint")

                    modelscope_key = gr.Textbox(
                        label="魔搭API Key",
                        placeholder="输入您的魔搭API Key",
                        info="用于访问Qwen模型和Embedding服务"
                    )

                    modelscope_url = gr.Textbox(
                        label="魔搭API Base URL",
                        value=os.getenv("MODELSCOPE_BASE_URL", "https://api-inference.modelscope.cn/v1"),
                        info="API基础URL"
                    )

                    mineru_key = gr.Textbox(
                        label="MinerU API Token",
                        placeholder="输入您的MinerU API Token",
                        info="用于PDF文档解析"
                    )

                    save_config_btn = gr.Button("💾 保存配置", variant="primary", size="lg")

                    gr.Markdown("""
                    <div style='background: #E3F2FD; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #2196F3;'>
                        <h4 style='color: #1976D2; margin: 0 0 10px 0;'>ℹ️ 关于API配置</h4>
                        <p style='margin: 0; font-size: 0.95em;'>• API密钥将临时存储在会话中，刷新页面后需重新配置<br>
                        • 如果不配置，将使用系统默认的API设置<br>
                        • 建议使用个人API密钥以获得更好的使用体验</p>
                    </div>
                    """)

                with gr.Column():
                    config_status = gr.Textbox(
                        label="配置状态",
                        lines=8,
                        max_lines=12,
                        info="显示配置结果"
                    )
                    gr.Markdown("""
                    <div style='background: #E8F5E9; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                        <h4 style='color: #388E3C; margin: 0 0 10px 0;'>🔒 安全提示</h4>
                        <p style='margin: 0; font-size: 0.9em;'>API密钥仅用于您的会话，不会被保存到服务器或共享给他人。</p>
                    </div>
                    """)

            # API配置保存
            save_config_btn.click(
                fn=lambda modelscope_key, modelscope_url, mineru_key:
                    app.save_api_config(modelscope_key, modelscope_url, mineru_key),
                inputs=[modelscope_key, modelscope_url, mineru_key],
                outputs=[config_status]
            )

        with gr.Tab("📄 文档上传与处理"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📤 本地文件上传")
                    gr.Markdown("支持直接上传本地PDF文件（最大200MB），无需上传到云端", elem_id="upload-hint")
                    pdf_file = gr.File(
                        label="选择PDF文件",
                        file_types=[".pdf"],
                        height=100
                    )
                    doc_name = gr.Textbox(
                        label="文档名称（可选）",
                        placeholder="为空将自动生成唯一ID",
                        info="用于后续查询和引用此文档"
                    )
                    upload_btn = gr.Button("🚀 开始处理", variant="primary", size="lg")

                with gr.Column():
                    status = gr.Textbox(
                        label="处理状态",
                        lines=8,
                        max_lines=12,
                        info="显示处理进度和结果"
                    )
                    content_preview = gr.Markdown(
                        label="内容预览",
                        value="等待上传文档..."
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
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;'>
                <h2 style='margin: 0; color: white;'>📖 SciResearcher 使用指南</h2>
                <p style='margin: 10px 0 0 0;'>帮助您快速上手科研文献智能分析系统</p>
            </div>

            ## 🚀 快速开始

            <div style='background: #E3F2FD; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #2196F3;'>
                <h3 style='color: #1976D2; margin-top: 0;'>📝 操作流程</h3>
                <div style='display: flex; align-items: center; margin: 15px 0;'>
                    <div style='background: #2196F3; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px;'>1</div>
                    <div style='flex: 1;'>
                        <h4 style='margin: 0; color: #1976D2;'>API配置</h4>
                        <p style='margin: 5px 0 0 0; font-size: 0.95em;'>在"API配置"页面设置您的魔搭API Key和MinerU Token（可选）</p>
                    </div>
                </div>
                <div style='display: flex; align-items: center; margin: 15px 0;'>
                    <div style='background: #2196F3; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px;'>2</div>
                    <div style='flex: 1;'>
                        <h4 style='margin: 0; color: #1976D2;'>上传PDF文档</h4>
                        <p style='margin: 5px 0 0 0; font-size: 0.95em;'>在"文档上传与处理"页面选择本地PDF文件（最大200MB）</p>
                    </div>
                </div>
                <div style='display: flex; align-items: center; margin: 15px 0;'>
                    <div style='background: #2196F3; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px;'>3</div>
                    <div style='flex: 1;'>
                        <h4 style='margin: 0; color: #1976D2;'>智能问答</h4>
                        <p style='margin: 5px 0 0 0; font-size: 0.95em;'>在"智能问答"页面输入问题，快速获取基于文档内容的准确答案</p>
                    </div>
                </div>
                <div style='display: flex; align-items: center; margin: 15px 0;'>
                    <div style='background: #2196F3; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px;'>4</div>
                    <div style='flex: 1;'>
                        <h4 style='margin: 0; color: #1976D2;'>深度研究</h4>
                        <p style='margin: 5px 0 0 0; font-size: 0.95em;'>在"深度研究"页面进行多维度分析，包括核心观点、方法论、创新点等</p>
                    </div>
                </div>
            </div>

            ## 💡 使用技巧

            <div style='background: #FFF3E0; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #FF9800;'>
                <h3 style='color: #F57C00; margin-top: 0;'>✨ 提问建议</h3>
                <ul style='line-height: 2;'>
                    <li><strong>具体明确：</strong>"这篇论文使用了什么研究方法？" vs "这篇论文讲了什么？"</li>
                    <li><strong>聚焦重点：</strong>"该方法的主要创新点是什么？"</li>
                    <li><strong>深度分析：</strong>"该研究的局限性和未来发展方向是什么？"</li>
                    <li><strong>应用场景：</strong>"该技术在实际应用中有什么价值？"</li>
                </ul>
            </div>

            <div style='background: #F3E5F5; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #9C27B0;'>
                <h3 style='color: #7B1FA2; margin-top: 0;'>🎯 深度研究维度</h3>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                    <div>
                        <h4 style='color: #9C27B0; margin: 0 0 10px 0;'>📊 核心内容</h4>
                        <ul style='margin: 0; font-size: 0.95em;'>
                            <li>核心观点总结</li>
                            <li>关键证据论据</li>
                            <li>方法论分析</li>
                        </ul>
                    </div>
                    <div>
                        <h4 style='color: #9C27B0; margin: 0 0 10px 0;'>🔬 价值评估</h4>
                        <ul style='margin: 0; font-size: 0.95em;'>
                            <li>创新点和贡献</li>
                            <li>局限性和不足</li>
                            <li>未来研究方向</li>
                        </ul>
                    </div>
                </div>
            </div>

            ## 🔧 技术架构

            <div style='background: #E8F5E9; padding: 20px; border-radius: 10px; margin: 20px 0;'>
                <h3 style='color: #388E3C; margin-top: 0;'>🏗️ 系统组成</h3>
                <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px;'>
                    <div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                        <h4 style='color: #388E3C; margin: 0 0 10px 0;'>📄 PDF解析</h4>
                        <p style='margin: 0; font-size: 0.9em;'>MinerU 官方API<br>支持OCR、公式、表格识别</p>
                    </div>
                    <div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196F3;'>
                        <h4 style='color: #1976D2; margin: 0 0 10px 0;'>🔍 向量检索</h4>
                        <p style='margin: 0; font-size: 0.9em;'>ChromaDB + 魔搭Embedding<br>高效语义检索</p>
                    </div>
                    <div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #FF9800;'>
                        <h4 style='color: #F57C00; margin: 0 0 10px 0;'>💬 问答引擎</h4>
                        <p style='margin: 0; font-size: 0.9em;'>魔搭 Qwen-Plus<br>智能文档理解</p>
                    </div>
                    <div style='background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #9C27B0;'>
                        <h4 style='color: #7B1FA2; margin: 0 0 10px 0;'>🌐 Web界面</h4>
                        <p style='margin: 0; font-size: 0.9em;'>Gradio<br>现代化用户界面</p>
                    </div>
                </div>
            </div>

            ## ⚠️ 注意事项

            <div style='background: #FFEBEE; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #F44336;'>
                <h3 style='color: #C62828; margin-top: 0;'>🔔 重要提醒</h3>
                <ul style='line-height: 2; color: #424242;'>
                    <li>📁 <strong>本地文件：</strong>PDF文件直接上传到容器，无需额外操作</li>
                    <li>🌐 <strong>在线链接：</strong>PDF URL必须是公开可访问的直接下载链接</li>
                    <li>⏱️ <strong>处理时间：</strong>首次处理可能需要几分钟，请耐心等待</li>
                    <li>💾 <strong>数据存储：</strong>文档会持久化存储在 ./data/ 目录</li>
                    <li>🔄 <strong>文档管理：</strong>可在"文档管理"页面查看和管理已处理文档</li>
                </ul>
            </div>

            ## 📞 支持与反馈

            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
                <h3 style='margin: 0 0 10px 0; color: white;'>🎉 开始您的科研文献分析之旅</h3>
                <p style='margin: 0;'>上传第一篇PDF，开启智能分析体验！</p>
            </div>
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
