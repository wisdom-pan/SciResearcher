# SciResearcher

> 基于 smolagents + MinerU API + ChromaDB 的科研文献深度理解框架

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![smolagents](https://img.shields.io/badge/smolagents-1.0+-green.svg)](https://github.com/huggingface/smolagents)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Gradio](https://img.shields.io/badge/Gradio-Web_UI-orange.svg)](https://gradio.app/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## 📋 目录

- [快速开始](#快速开始)
- [Docker部署](#docker-部署)
- [本地安装](#本地安装)
- [Web界面功能](#web-界面功能)
- [API配置](#api-配置)
- [项目结构](#项目结构)
- [详细使用指南](#详细使用指南)
- [故障排除](#故障排除)

## 项目简介

SciResearcher 是专为科研工作者设计的轻量、开源、可验证的 AI 助手。基于 **smolagents** + **MinerU API** + **ChromaDB** + **魔搭API**，提供科研文献的智能解析、问答和深度研究功能。

### 核心特点

- ✅ **Web 界面**: 基于 Gradio 的现代化 Web 交互界面
- ✅ **MinerU API 解析**: 支持 PDF 多模态解析（文字、图表、公式、OCR）
- ✅ **魔搭 API**: 集成 Qwen-Plus 进行智能问答和深度分析
- ✅ **ChromaDB 向量库**: 高效语义检索，支持文档管理
- ✅ **smolagents 框架**: 使用 HuggingFace 官方 Multi-Agent 框架
- ✅ **可验证输出**: 强制引用 + 置信度评分
- ✅ **Docker 部署**: 一键部署，开箱即用

### v2.1.0 重大更新

🎉 **全新 Web 界面 + API 调用模式**

- 🌐 **Gradio Web UI**: 全新的现代化 Web 界面，支持文档上传、智能问答、深度研究
- 🔗 **API 模式**: 使用 MinerU API + 魔搭 API，无需本地部署模型
- 💾 **ChromaDB**: 提供更好的文档管理和持久化
- ⚙️ **自定义配置**: 支持用户自定义 API Key 和 Token

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      SciResearcher                          │
│                   Gradio Web Interface                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    核心功能模块                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  文档上传     │  │  智能问答     │  │  深度研究     │     │
│  │  PDF处理     │  │  RAG检索     │  │  多维分析     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       工具集 (Tools)                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ parse_pdf()          # MinerU API PDF解析          │    │
│  │ vector_db.add()      # ChromaDB 文档索引           │    │
│  │ vector_db.search()   # 语义检索                    │    │
│  │ ask_question()       # 智能问答                    │    │
│  │ deep_research()      # 深度研究分析                │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      API 服务层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 魔搭 Qwen    │  │  MinerU API  │  │  ChromaDB    │     │
│  │  Plus/Turbo  │  │  PDF解析     │  │  向量检索     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ 魔搭 Embed   │  │   Qwen-VL    │                       │
│  │   向量化      │  │   视觉理解   │                       │
│  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 🐳 方式一：Docker 部署（推荐）

使用 Docker 快速启动 SciResearcher，无需手动安装依赖！

#### 前置条件
- Docker [下载地址](https://www.docker.com/products/docker-desktop)
- Docker Compose [下载地址](https://docs.docker.com/compose/install/)

#### 部署步骤

1. **克隆项目**
```bash
git clone https://github.com/your-repo/SciResearcher.git
cd SciResearcher
```

2. **配置环境变量**
```bash
cp .env.example .env
```
编辑 `.env` 文件，填入您的API密钥：
```bash
MODELSCOPE_API_KEY=您的魔搭API密钥
MINERU_API_TOKEN=您的MinerU Token
```

3. **使用 Docker Compose 启动**
```bash
# 构建并启动所有服务
docker-compose up -d

# 或仅启动Web应用
docker-compose up --build -d
```

4. **访问应用**
打开浏览器访问: http://localhost:7860

#### Docker 命令

```bash
# 构建镜像
docker build -t sciresearcher .

# 运行容器
docker run -d \
  --name sciresearcher \
  -p 7860:7860 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  sciresearcher

# 查看日志
docker logs -f sciresearcher

# 停止容器
docker-compose down
```

### 💻 方式二：本地安装

如果不想使用Docker，可以直接本地安装：

```bash
# 1. 创建虚拟环境
conda create -n sciresearcher python=3.10
conda activate sciresearcher

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 4. 启动 Web 界面
python gradio_app.py
# 访问: http://localhost:7860
```

### 🌐 方式三：魔搭创空间部署

一键部署到 [魔搭创空间](https://www.modelscope.cn/studios/)，无需本地配置！

#### 📋 准备工作

在开始部署前，您需要准备：

1. **创建魔搭账号**
   - 访问 [魔搭社区](https://www.modelscope.cn/)
   - 注册并登录账号

2. **创建访问Token**
   - 访问 [访问Token页面](https://www.modelscope.cn/my/accesstoken)
   - 点击"创建新的访问Token"
   - 复制生成的Token（格式：ms-xxxxx）

3. **创建创空间**
   - 访问 [创空间页面](https://www.modelscope.cn/studios/)
   - 点击"创建创空间"
   - 选择"Blank App"模板
   - 填写项目名称（如：MySciResearcher）
   - 创建后会得到您的用户名和项目名

#### 🚀 自动部署（推荐）

1. **创建配置文件**
   ```bash
   # 复制配置模板
   cp deploy_config.example deploy_config.sh

   # 编辑配置文件
   nano deploy_config.sh  # 或使用其他编辑器

   # 修改以下配置：
   MODELSCOPE_TOKEN="ms-您的访问Token"
   USERNAME="您的用户名"
   PROJECT_NAME="您的项目名"
   ```

2. **运行部署脚本**
   ```bash
   # 确保脚本有执行权限
   chmod +x deploy_to_studio.sh

   # 运行部署脚本
   ./deploy_to_studio.sh
   ```

   脚本会自动完成：
   - ✅ 读取配置文件
   - ✅ 验证配置信息
   - ✅ 安装 git lfs
   - ✅ 克隆您的创空间仓库
   - ✅ 同步项目文件
   - ✅ 提交并推送到创空间

#### 💡 配置文件说明

`deploy_config.sh` 是部署配置文件，包含以下配置项：

```bash
# 必需配置
MODELSCOPE_TOKEN="ms-您的访问Token"    # 魔搭访问Token
USERNAME="您的用户名"                   # 魔搭用户名
PROJECT_NAME="您的项目名"              # 创空间项目名

# 可选配置
PROJECT_DIR="."                        # 项目本地路径
BRANCH="master"                        # Git分支
```

**安全提示**：
- `deploy_config.sh` 包含敏感信息，建议添加到 `.gitignore`
- 不要将包含Token的配置文件提交到版本控制

#### 📝 手动部署

如果您想手动部署，按以下步骤：

1. **克隆您的创空间仓库**
   ```bash
   git lfs install
   git clone http://oauth2:您的Token@www.modelscope.cn/studios/您的用户名/您的项目名.git
   cd 您的项目名
   ```

2. **复制项目文件**
   ```bash
   # 从本项目复制文件到仓库
   rsync -av --exclude='.git' /path/to/源项目/ ./
   ```

3. **提交并推送**
   ```bash
   git add .
   git commit -m "🚀 Deploy SciResearcher to ModelScope Studio"
   git push origin master
   ```

#### ⚙️ 部署后配置

1. **访问您的创空间**
   - URL: https://www.modelscope.cn/studios/您的用户名/您的项目名

2. **配置环境变量**
   - 点击右上角"设置"按钮
   - 进入"环境变量"页面
   - 添加以下变量：
     - `MODELSCOPE_API_KEY`: 您的魔搭API密钥（用于调用Qwen模型）
     - `MINERU_API_TOKEN`: 您的MinerU Token（用于PDF解析）
   - 点击保存

3. **等待构建完成**
   - 创空间会自动开始构建
   - 首次构建需要5-10分钟
   - 状态会显示在创空间页面

4. **开始使用**
   - 构建完成后即可访问应用
   - 上传PDF文档开始分析

#### ✅ 创空间特性

- ✅ **零配置**: 无需服务器或Docker知识
- ✅ **自动扩展**: 根据访问量自动调整资源
- ✅ **公开分享**: 自动生成可分享的链接
- ✅ **环境隔离**: 每个应用独立运行环境
- ✅ **免费使用**: 魔搭社区提供免费额度

## 📸 界面演示

![SciResearcher Demo](assets/demo.jpeg)

## API 配置

### 获取魔搭 API 密钥

1. 访问 [魔搭社区控制台](https://dashscope.console.aliyun.com/apiKey)
2. 创建 API Key
3. 将密钥填入 `.env` 文件的 `MODELSCOPE_API_KEY`

### 获取 MinerU API Token

1. 访问 [MinerU 控制台](https://mineru.net)
2. 注册并获取 API Token
3. 将 Token 填入 `.env` 文件的 `MINERU_API_TOKEN`

### 环境变量配置

```bash
# .env 文件
MODELSCOPE_API_KEY=your_api_key
MODELSCOPE_BASE_URL=https://api-inference.modelscope.cn/v1
MINERU_API_TOKEN=your_token
```

## 项目结构

```
SciResearcher/
├── app.py                      # Docker 入口点
├── gradio_app.py               # Web 界面主程序
├── tools/
│   ├── smolagents_tools.py      # MinerU 工具
│   └── vector_db_chroma.py      # ChromaDB 向量库
├── config/
│   └── config.yaml             # 配置文件
├── data/                        # 数据存储目录
│   ├── chromadb/               # ChromaDB 向量库数据
│   ├── uploads/                # 上传的PDF文件
│   └── logs/                   # 应用日志
├── Dockerfile                   # Docker 镜像构建文件
├── docker-compose.yml          # Docker Compose 编排配置
├── requirements.txt            # Python 依赖列表
├── .env.example               # 环境变量模板
└── README.md                   # 本文档
```

## 🐳 Docker 部署说明

### Dockerfile 配置
- 基于 `modelscope/python:3.10` 镜像
- 自动安装依赖
- 暴露 7860 端口
- 使用 `app.py` 作为启动入口

### Docker Compose 服务
- **sciresearcher**: 主应用服务
  - 构建: `./` 目录
  - 端口映射: `7860:7860`
  - 环境变量: 从 `.env` 文件读取
  - 数据卷: 挂载 `./data` 和 `./logs` 目录

## 开发指南

### 添加新功能

在 `tools/smolagents_tools.py` 中添加新的 smolagents 工具：

```python
from smolagents import tool

@tool
def your_new_tool(param: str) -> str:
    """
    Tool description here.

    Args:
        param: Parameter description

    Returns:
        Result description
    """
    # Your implementation
    return result
```

### 运行测试

```bash
pytest tests/
```

## 常见问题

### Q: 如何提高回答质量?

A:
1. 使用更强的模型 (qwen-plus)
2. 增加检索结果数量
3. 优化文本分块大小

### Q: 支持哪些 PDF 格式?

A: 支持标准 PDF 格式，包括:
- 文本型 PDF
- 扫描型 PDF (支持 OCR)
- 包含图表、公式的学术论文

### Q: 文档数据如何存储?

A: 文档内容持久化存储在 `./data/chromadb/` 目录中，容器重启后数据不会丢失。

## 致谢

- [smolagents](https://github.com/huggingface/smolagents) - HuggingFace 的 Multi-Agent 框架
- [Qwen](https://github.com/QwenLM/Qwen) - 阿里云通义千问系列模型
- [MinerU](https://github.com/opendatalab/MinerU) - PDF 解析工具
- [ChromaDB](https://github.com/chroma-core/chroma) - 开源向量数据库
- [Gradio](https://gradio.app/) - 机器学习 Web 界面框架

---

**🌟 如果这个项目对您有帮助，请给个 Star！**

**📧 联系方式**: your-email@example.com

---

## 📖 详细使用指南

### 🎯 第一步：获取API密钥

#### 1. 获取魔搭 API 密钥
1. 访问 [魔搭社区控制台](https://dashscope.console.aliyun.com/apiKey)
2. 登录并创建 API Key
3. 复制密钥备用

#### 2. 获取 MinerU API Token
1. 访问 [MinerU 控制台](https://mineru.net)
2. 注册账号并获取 API Token
3. 复制 Token 备用

### 🚀 第二步：启动应用

#### 本地启动
```bash
python gradio_app.py
# 访问 http://localhost:7860
```

#### 创空间启动
访问您的创空间链接即可

### 📄 第三步：配置API

1. 点击 "⚙️ API配置" 标签页
2. 填入您的魔搭API Key 和 MinerU Token
3. 点击 "💾 保存配置"

### 📚 第四步：上传文档

1. 点击 "📄 文档上传与处理" 标签页
2. 选择本地PDF文件（最大200MB）
3. 点击 "🚀 开始处理"
4. 等待处理完成

### 💬 第五步：智能问答

1. 点击 "💬 智能问答" 标签页
2. 输入您的问题，例如：
   - "这篇论文的主要贡献是什么？"
   - "该研究使用了什么方法？"
3. 点击 "🤔 开始问答"

### 🎯 第六步：深度研究

1. 点击 "🎯 深度研究" 标签页
2. 输入研究问题，例如：
   - "分析这篇论文的方法论和创新点"
   - "评估该研究的实际应用价值"
   - "探讨研究的局限性和未来方向"
3. 点击 "🔬 开始深度研究"

### 📚 第七步：文档管理

1. 点击 "📚 文档管理" 标签页
2. 查看已处理文档列表
3. 可清空数据库重新开始

---

## ⚡ 快速体验流程（Docker部署）

```
1️⃣ 克隆项目 → 2️⃣ 配置.env → 3️⃣ docker-compose up → 4️⃣ 访问 http://localhost:7860 → 5️⃣ 上传PDF测试
```

### 极简步骤（复制粘贴）

```bash
# 一键部署
git clone https://github.com/your-repo/SciResearcher.git
cd SciResearcher
cp .env.example .env  # 编辑.env填入API密钥
docker-compose up -d  # 启动
# 访问 http://localhost:7860
```

💡 **提示**: 首次使用建议先上传一篇较短的PDF文档测试，确认所有功能正常后再处理长文档。

---

## 🔧 故障排除

### 常见问题

**Q: PDF上传失败？**
A: 检查文件大小是否超过200MB，或文件格式是否正确

**Q: API调用失败？**
A: 检查网络连接和API密钥是否正确

**Q: 问答结果不准确？**
A: 尝试重新上传文档，或使用更具体的问题

**Q: 处理速度慢？**
A: 大文档需要更长时间，请耐心等待。可查看进度日志了解状态。

**Q: Docker容器启动失败？**
A: 检查Docker是否正常运行，执行 `docker version` 确认

**Q: Docker Compose无法启动？**
A: 检查端口7860是否被占用，或尝试执行 `docker-compose down` 停止后重新启动

**Q: 容器内部错误？**
A: 查看容器日志执行 `docker logs sciresearcher`

**Q: 数据卷未挂载？**
A: 确保 `.env` 文件存在且配置正确，检查 data/ 目录权限

### 💡 API密钥获取指南

#### 获取魔搭 API 密钥
1. 访问 [魔搭社区控制台](https://dashscope.console.aliyun.com/apiKey)
2. 登录阿里云账号（如果未登录）
3. 点击"创建新的API-KEY"
4. 复制生成的API Key（格式：sk-xxxxxxxx）

#### 获取魔搭访问Token（用于Git推送）
1. 访问 [魔搭访问Token页面](https://www.modelscope.cn/my/accesstoken)
2. 点击"创建新的访问Token"
3. 填写Token名称（如：DeployToken）
4. 设置过期时间（建议长期）
5. 复制生成的Token（格式：ms-xxxxxxxx）

#### 获取 MinerU Token
1. 访问 [MinerU官网](https://mineru.net)
2. 注册账号并登录
3. 进入控制台
4. 在API Token页面创建新Token
5. 复制Token备用

### 🚀 创空间使用指南

#### 创建创空间
1. 访问 [创空间页面](https://www.modelscope.cn/studios/)
2. 点击右上角"创建创空间"
3. 填写信息：
   - 名称：项目显示名称
   - 描述：项目功能描述
   - 分类：选择"工具类"或"应用类"
4. 选择"Blank App"模板
5. 点击"创建"

#### 配置环境变量
1. 在创空间页面点击右上角"设置"
2. 选择"环境变量"选项卡
3. 点击"添加变量"
4. 添加以下变量：
   - 变量名：`MODELSCOPE_API_KEY`，值：您的魔搭API Key
   - 变量名：`MINERU_API_TOKEN`，值：您的MinerU Token
5. 点击"保存"
6. 重启应用（点击"重启"按钮）

#### 监控构建状态
- 在创空间页面可以查看实时构建日志
- 构建成功后会显示"运行中"状态
- 如构建失败，日志中会显示具体错误信息

#### 分享应用
- 创空间自动生成公开访问链接
- 可在社交媒体或文档中分享链接
- 其他人可直接访问和使用

### 🔍 故障诊断

#### 如果应用无法访问
1. 检查构建状态是否为"运行中"
2. 查看设置中的环境变量是否正确配置
3. 检查构建日志是否有错误

#### 如果API调用失败
1. 验证API密钥是否有效（未过期）
2. 检查网络连接
3. 确认API密钥有足够额度

#### 如果上传PDF失败
1. 确认文件格式为PDF
2. 检查文件大小不超过200MB
3. 确认文件未被密码保护

---

## 📞 获取帮助

如果您遇到问题，可以：

1. **查看文档**: 阅读本README文档
2. **检查日志**: 在创空间查看构建和运行日志
3. **提交Issue**: 在GitHub仓库提交问题
4. **社区讨论**: 在魔搭社区提问

---

## 🎯 最佳实践

1. **首次使用**: 建议先用小文档测试整个流程
2. **API密钥**: 定期检查密钥有效性和额度
3. **文档管理**: 定期清理不需要的文档
4. **问题反馈**: 遇到问题时及时记录和反馈
