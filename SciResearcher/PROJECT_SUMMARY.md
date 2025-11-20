# SciResearcher 项目实现总结

## 项目概述

SciResearcher 是一个完全基于 **smolagents** 框架、**Qwen3 系列模型** 和 **MinerU** 的科研文献深度理解系统，所有功能通过 API 调用实现，架构完全解耦。

## 技术架构

### 核心技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **Agent 框架** | smolagents | HuggingFace 官方 Multi-Agent 框架 |
| **LLM** | Qwen3 (qwen-plus/turbo/max) | 通过阿里云百炼 API |
| **Embedding** | Qwen3 text-embedding-v3 | 向量化模型 |
| **Vision** | Qwen-VL (qwen-vl-max) | 图像理解 |
| **PDF 解析** | MinerU API / 本地 MinerU | 多模态 PDF 解析 |
| **向量数据库** | FAISS | 高效向量检索 |
| **部署** | Docker + Docker Compose | 容器化部署 |

### 架构特点

1. **完全 API 化**: 所有模型通过 API 调用，无需本地部署
2. **基于 smolagents**: 使用官方 Agent 框架，而非自建 Agent
3. **工具解耦**: 每个功能封装为 `@tool`，可独立使用
4. **灵活扩展**: 轻松添加新工具和功能

## 项目结构

```
SciResearcher/
├── main.py                      # 主程序 - 基于 smolagents 的系统
├── tools/
│   └── research_tools.py        # smolagents 工具集 (5个工具)
├── config/
│   ├── __init__.py             # 配置加载器
│   └── config.yaml             # YAML 配置
├── data/                        # 数据目录
│   ├── pdfs/                   # 原始 PDF
│   ├── processed/              # 处理后数据
│   ├── vector_index/           # 向量索引
│   └── cache/                  # 缓存
├── Dockerfile                   # Docker 镜像定义
├── docker-compose.yml          # Docker Compose 配置
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量模板
├── start.sh                    # 快速启动脚本
└── README.md                   # 项目文档
```

## 核心功能实现

### 1. smolagents 工具集 (tools/research_tools.py)

实现了 5 个核心工具:

#### ① parse_pdf_with_mineru
- **功能**: 使用 MinerU API 解析 PDF
- **提取内容**: 文字、图片、表格、公式
- **API 调用**: MinerU REST API (可配置)
- **回退方案**: 本地 MinerU 库

#### ② index_documents
- **功能**: 文本分块和向量化
- **向量化**: Qwen3 Embedding API (text-embedding-v3)
- **存储**: FAISS 向量数据库
- **分块策略**: 按句子分割，支持 overlap

#### ③ search_documents
- **功能**: 语义搜索
- **检索**: 基于 FAISS 的相似度搜索
- **返回**: Top-K 结果 + 相似度分数

#### ④ analyze_image
- **功能**: 图表理解
- **模型**: Qwen-VL API (qwen-vl-max)
- **支持**: 图表、架构图、公式图片

#### ⑤ process_research_paper
- **功能**: 综合处理流程
- **步骤**: PDF 解析 → 文本索引 → 返回摘要

### 2. Multi-Agent 系统 (main.py)

基于 smolagents 的 SciResearcher 类:

```python
class SciResearcher:
    def __init__(self, model_name, agent_type):
        # 1. 初始化 Qwen3 模型 (通过 LiteLLM)
        self.model = LiteLLMModel(...)

        # 2. 加载 smolagents 工具
        self.tools = [
            process_research_paper,
            parse_pdf_with_mineru,
            index_documents,
            search_documents,
            analyze_image
        ]

        # 3. 创建 Agent
        if agent_type == "tool-calling":
            self.agent = ToolCallingAgent(...)
        else:
            self.agent = CodeAgent(...)
```

#### 核心方法

- `process_pdf()`: 处理 PDF 文件
- `answer_question()`: 回答科研问题
- `analyze_figures()`: 分析图表
- `comprehensive_research()`: 完整研究分析
- `multi_paper_synthesis()`: 多文档综合分析

## API 配置

### 阿里云百炼 API

**获取地址**: https://dashscope.console.aliyun.com/apiKey

**支持的模型**:
- `qwen-plus`: 平衡性能和成本（推荐）
- `qwen-turbo`: 快速响应
- `qwen-max`: 最强性能
- `text-embedding-v3`: Qwen3 Embedding
- `qwen-vl-max`: Qwen-VL 视觉理解

### MinerU API（可选）

如果有 MinerU 服务，可配置 API URL 和 Key，否则使用本地 MinerU 库。

## Docker 部署

### Dockerfile

- **基础镜像**: `python:3.10-slim`
- **依赖安装**: requirements.txt + MinerU wheels
- **数据卷**: `/app/data`, `/app/logs`
- **入口点**: `main.py`

### docker-compose.yml

```yaml
services:
  sciresearcher:
    build: .
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    stdin_open: true
    tty: true
```

### 一键部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 2. 启动容器
docker-compose up -d

# 3. 进入容器
docker exec -it sciresearcher bash

# 4. 运行
python main.py
```

## 使用示例

### 命令行模式

```bash
# 处理 PDF
python main.py --pdf paper.pdf

# 回答问题
python main.py --question "Transformer的优势?"

# 完整分析
python main.py --pdf paper.pdf --question "主要贡献?"

# 图表分析
python main.py --images fig1.png fig2.png
```

### Python API

```python
from main import SciResearcher

# 初始化
researcher = SciResearcher(
    model_name="qwen-plus",
    agent_type="tool-calling"
)

# 处理 PDF
result = researcher.process_pdf("paper.pdf")

# 回答问题
answer = researcher.answer_question(
    "Transformer相比LSTM有什么优势?",
    require_citations=True
)

# 多文档综合
synthesis = researcher.multi_paper_synthesis(
    pdf_paths=["paper1.pdf", "paper2.pdf"],
    research_question="研究问题"
)
```

## 关键设计决策

### 1. 为什么选择 smolagents?

- ✅ HuggingFace 官方框架，维护稳定
- ✅ 支持 ToolCallingAgent 和 CodeAgent
- ✅ 与 LiteLLM 无缝集成
- ✅ 简单的 `@tool` 装饰器

### 2. 为什么全部使用 API?

- ✅ 无需本地部署大模型，降低硬件要求
- ✅ 按需付费，成本可控
- ✅ 模型随时更新，无需重新下载
- ✅ 支持 Docker 轻量化部署

### 3. 为什么使用 FAISS?

- ✅ 高效的向量检索
- ✅ 支持 CPU 和 GPU
- ✅ 无需额外服务器
- ✅ 易于持久化

## 扩展指南

### 添加新工具

在 `tools/research_tools.py`:

```python
@tool
def new_research_tool(param: str) -> str:
    """
    Tool description for LLM to understand.

    Args:
        param: Parameter description

    Returns:
        Result description
    """
    # Implementation
    return result
```

在 `main.py` 注册:

```python
from tools.research_tools import new_research_tool

self.tools = [
    # existing tools
    new_research_tool
]
```

### 更换 LLM

修改 `main.py`:

```python
# 使用 OpenAI
self.model = LiteLLMModel(
    model_id="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
)

# 使用其他兼容 OpenAI API 的模型
self.model = LiteLLMModel(
    model_id="openai/your-model",
    api_key=...,
    api_base="https://your-api-url"
)
```

## 性能优化

### 1. 向量检索优化

- 调整 `chunk_size` 和 `chunk_overlap`
- 增加 `top_k` 获取更多候选结果
- 使用 GPU 版本的 FAISS

### 2. API 调用优化

- 使用 `qwen-turbo` 加快响应
- 启用缓存减少重复调用
- 批量处理多个请求

### 3. 内存优化

- 定期清理向量数据库
- 限制索引文档数量
- 使用增量索引

## 未来规划

### 短期 (1-2个月)

- [ ] Web 界面
- [ ] 多文档综述功能
- [ ] 实验设计建议
- [ ] 研究空白探测

### 中期 (3-6个月)

- [ ] MCP Server 封装
- [ ] 插件系统
- [ ] API 服务
- [ ] 性能监控

### 长期 (6-12个月)

- [ ] 多语言支持
- [ ] 私有部署方案
- [ ] 企业级功能
- [ ] 社区生态

## 参考文档

- [smolagents 官方文档](https://github.com/huggingface/smolagents)
- [Qwen 模型文档](https://help.aliyun.com/zh/dashscope/)
- [MinerU 项目](https://github.com/opendatalab/MinerU)
- [FAISS 文档](https://github.com/facebookresearch/faiss)

## 总结

SciResearcher 成功实现了一个完全基于 API 的科研文献理解系统，核心特点：

1. ✅ **架构解耦**: smolagents 框架 + 工具集分离
2. ✅ **API 优先**: 所有模型通过 API 调用
3. ✅ **易于部署**: Docker 一键部署
4. ✅ **可扩展**: 简单添加新工具和功能
5. ✅ **开源友好**: MIT 协议，完全开源

项目已准备好用于:
- 科研文献分析
- 学术论文问答
- 图表理解
- 多文档综述
- 比赛提交

---

**项目地址**: https://github.com/your-repo/SciResearcher
**作者**: Your Name
**更新时间**: 2024
