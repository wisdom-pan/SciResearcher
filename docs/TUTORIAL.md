# SciResearcher 初学者教程 (MVP版本)

> 🎯 **目标**: 30分钟从零开始,学会运行和使用科研文献分析系统

---

## 📚 快速导航

- **5分钟了解**: [这个系统是什么](#这个系统是什么)
- **10分钟安装**: [环境准备和安装](#环境准备)
- **15分钟上手**: [第一次使用](#第一次使用)
- **进阶学习**: [深入理解](#深入理解)

---

## 这个系统是什么?

### 一句话介绍

**SciResearcher** = 一个会"读论文"的AI助手,可以理解PDF中的文字、图表、公式,然后回答你的问题。

### 能做什么?

```
你问: "这篇论文的创新点是什么?"
    ↓
系统: 1️⃣ 解析PDF (提取文字+图表+公式)
     2️⃣ 理解图表 (用AI看懂图)
     3️⃣ 检索证据 (找相关内容)
     4️⃣ 生成答案 (基于证据回答)
     5️⃣ 质量检查 (确保答案可靠)
    ↓
输出: "这篇论文的创新点是...
      - 创新点1: xxx (见第3页图2)
      - 创新点2: xxx (见表1)
      置信度: 0.85"
```

### 为什么特别?

| 传统方法 | SciResearcher |
|---------|---------------|
| ❌ 只能读文字,看不懂图表 | ✅ 文字+图表+公式全都懂 |
| ❌ 容易瞎编答案 | ✅ 有证据+引用+置信度 |
| ❌ 一个AI做所有事 | ✅ 5个AI协作(专业分工) |

---

## 核心概念 (3分钟理解)

### 1. 什么是 Multi-Agent (多智能体)?

**就像一个研究团队**:

```
传统AI = 一个人做所有事情
    读论文 → 看图 → 回答 → 检查
    结果: 样样通,样样松

Multi-Agent = 5个人各司其职
    人1 (Planner)   → 拆解任务: "需要做3件事"
    人2 (Retriever) → 检索证据: "找到5段相关内容"
    人3 (Caption)   → 理解图表: "这张图说明了..."
    人4 (Reasoner)  → 推理回答: "基于证据,答案是..."
    人5 (Reviewer)  → 质量检查: "答案可靠,置信度0.85"
    结果: 专业分工,质量更高
```

### 2. 什么是 Vector Database (向量数据库)?

**就像一个"语义搜索引擎"**:

```
普通搜索 (关键词匹配):
    问题: "什么是深度学习?"
    只能找到包含"深度学习"这4个字的内容

向量搜索 (语义匹配):
    问题: "什么是深度学习?"
    能找到: "神经网络", "机器学习", "AI模型"
    原因: 理解"意思相近",不只是字面匹配
```

**我们用的是 ChromaDB**: 轻量、简单、自动保存

### 3. 系统架构 (3层设计)

```
┌─────────────────────────────────────────────┐
│              用户提问                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   Agents 层 (5个专门的AI)                   │
│   ├── Planner   → 任务分解                  │
│   ├── Retriever → 证据检索                  │
│   ├── Caption   → 图像理解                  │
│   ├── Reasoner  → 推理生成                  │
│   └── Reviewer  → 质量检查                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   Tools 层 (5个工具函数)                    │
│   ├── parse_pdf      → 解析PDF             │
│   ├── index_documents → 建立索引            │
│   ├── search_documents → 搜索内容           │
│   ├── analyze_image   → 分析图表            │
│   └── process_paper   → 完整流程            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   Services 层 (5个服务)                     │
│   ├── PDFService      → MinerU云服务        │
│   ├── VisionService   → Qwen-VL图像理解     │
│   ├── EmbeddingService → Qwen3向量化       │
│   ├── VectorStore     → ChromaDB存储        │
│   └── ModelFactory    → API客户端管理       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   外部API (云服务)                          │
│   ├── 阿里云 Dashscope (Qwen3模型)         │
│   └── MinerU云服务 (PDF解析)               │
└─────────────────────────────────────────────┘
```

**关键点**:
- ✅ **Agents层**: 5个AI协作
- ✅ **Tools层**: 简单的工具函数
- ✅ **Services层**: 核心功能实现
- ✅ **外部API**: 调用云服务 (不需要本地部署模型)

---

## 环境准备

### 第一步: 检查Python版本

```bash
python --version
# 需要: Python 3.9 或更高
```

**如果版本太低**:
- 去 https://www.python.org/downloads/ 下载最新版本
- 或使用 pyenv 安装: `pyenv install 3.11`

### 第二步: 获取API密钥

#### 2.1 阿里云 Dashscope API密钥

1. 访问: https://dashscope.console.aliyun.com/
2. 注册/登录阿里云账号
3. 点击右上角头像 → "API-KEY管理"
4. 点击"创建新的API-KEY"
5. 复制密钥 (格式: `sk-xxxxxxxxxxxxx`)

**免费额度**: 新用户有免费额度,够测试使用

#### 2.2 MinerU API Token

1. 访问: https://mineru.net/
2. 注册/登录账号
3. 进入"API管理"
4. 创建API Token
5. 复制token (格式: `sk-xxxxxxxxxxxxx`)

**免费额度**: 新用户有免费解析次数

### 第三步: 安装项目

```bash
# 1. 下载项目
git clone <repository-url>
cd SciResearcher

# 2. 创建虚拟环境 (推荐)
python -m venv venv

# 3. 激活虚拟环境
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt
```

**安装时间**: 大约3-5分钟

### 第四步: 配置环境变量

```bash
# 1. 复制示例文件
cp .env.example .env

# 2. 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

**填入你的API密钥**:

```bash
# 阿里云 Dashscope API密钥
DASHSCOPE_API_KEY=sk-你的Dashscope密钥

# MinerU API Token
MINERU_API_TOKEN=sk-你的MinerU Token
```

**⚠️ 注意**:
- 不要有引号
- 不要有空格
- 保存后关闭编辑器

---

## 第一次使用

### 示例1: 解析一篇论文 (最简单)

```python
from tools.research_tools import process_research_paper
import json

# 1. 准备一个公开的PDF链接 (必须是可直接访问的URL)
pdf_url = "https://arxiv.org/pdf/1706.03762.pdf"  # Transformer论文

# 2. 解析论文
result = process_research_paper(pdf_url)

# 3. 查看结果
data = json.loads(result)
print(f"✅ 解析完成!")
print(f"📝 文本长度: {data['text_length']} 字符")
print(f"📊 表格数量: {data['tables_count']} 个")
print(f"🖼️ 图片数量: {data['images_count']} 个")
```

**运行**:
```bash
python your_script.py
```

**预期输出**:
```
📤 提交 PDF: https://arxiv.org/pdf/1706.03762.pdf...
✅ 任务 ID: task_12345
📄 进度: 5/15 页
📄 进度: 10/15 页
📄 进度: 15/15 页
📥 下载结果...
📊 向量化 120 个文本块...
✅ 成功添加 120 个向量
💾 索引已保存: 120 个向量
✅ 解析完成!
📝 文本长度: 45823 字符
📊 表格数量: 3 个
🖼️ 图片数量: 8 个
```

### 示例2: 搜索论文内容

```python
from tools.research_tools import search_documents
import json

# 搜索问题
query = "什么是self-attention机制?"

# 执行搜索
results = search_documents(query, top_k=3)
data = json.loads(results)

# 显示结果
for i, result in enumerate(data, 1):
    print(f"\n📌 结果 {i}:")
    print(f"相关度分数: {result['score']:.2f}")
    print(f"内容摘要: {result['text'][:150]}...")
```

**预期输出**:
```
📌 结果 1:
相关度分数: 0.23
内容摘要: Self-attention, sometimes called intra-attention is an
attention mechanism relating different positions of a single...

📌 结果 2:
相关度分数: 0.31
内容摘要: The Transformer is the first transduction model relying
entirely on self-attention to compute representations...
```

### 示例3: 使用Agent完整流程

**创建文件**: `test_agent.py`

```python
from agents.research_agents import (
    PlannerAgent,
    RetrieverAgent,
    ReasonerAgent,
    ReviewerAgent
)

# 研究问题
question = "Transformer模型的核心创新是什么?"

print("🤔 研究问题:", question)
print("\n" + "="*50)

# 1️⃣ 任务分解
print("\n1️⃣ 任务分解中...")
planner = PlannerAgent()
plan = planner.plan(question)
print(f"📋 分解为 {len(plan['sub_tasks'])} 个子任务:")
for i, task in enumerate(plan['sub_tasks'], 1):
    print(f"   {i}. {task}")

# 2️⃣ 证据检索
print("\n2️⃣ 检索证据中...")
retriever = RetrieverAgent()
evidence = retriever.retrieve(plan['sub_tasks'], top_k=5)
total_evidence = sum(e['evidence_count'] for e in evidence)
print(f"🔍 找到 {total_evidence} 条证据")

# 3️⃣ 推理生成
print("\n3️⃣ 生成答案中...")
reasoner = ReasonerAgent()
answer = reasoner.reason(
    question=question,
    evidence=evidence,
    require_citations=True
)
print(f"💡 答案: {answer['answer']}")
print(f"📊 置信度: {answer['confidence']:.2f}")

# 4️⃣ 质量检查
print("\n4️⃣ 质量检查中...")
reviewer = ReviewerAgent()
review = reviewer.review(
    question=question,
    answer=answer['answer'],
    evidence=evidence,
    confidence=answer['confidence']
)
print(f"✅ 最终置信度: {review['final_confidence']:.2f}")
print(f"🔄 需要迭代: {'是' if review['need_iterate'] else '否'}")
if review['issues']:
    print(f"⚠️ 发现问题: {', '.join(review['issues'])}")

print("\n" + "="*50)
print("🎉 分析完成!")
```

**运行**:
```bash
python test_agent.py
```

**预期输出**:
```
🤔 研究问题: Transformer模型的核心创新是什么?

==================================================

1️⃣ 任务分解中...
📋 分解为 3 个子任务:
   1. 理解Transformer的架构设计
   2. 分析self-attention机制
   3. 对比传统RNN/LSTM模型

2️⃣ 检索证据中...
🔍 找到 15 条证据

3️⃣ 生成答案中...
💡 答案: Transformer模型的核心创新主要包括:
1. 完全基于attention机制,摒弃了循环结构
2. 引入multi-head self-attention
3. 位置编码(Positional Encoding)设计
...
📊 置信度: 0.87

4️⃣ 质量检查中...
✅ 最终置信度: 0.85
🔄 需要迭代: 否

==================================================
🎉 分析完成!
```

---

## 深入理解

### 文件结构解析

```
SciResearcher/
├── services/              # 核心服务 (5个文件)
│   ├── model_factory.py   # API客户端管理
│   ├── pdf_service.py     # PDF解析 (MinerU)
│   ├── vision_service.py  # 图像理解 (Qwen-VL)
│   ├── embedding_service.py # 文本向量化 (Qwen3)
│   └── vector_store.py    # 向量存储 (ChromaDB)
│
├── agents/                # AI智能体 (1个文件)
│   └── research_agents.py # 5个Agent类
│
├── tools/                 # 工具函数 (1个文件)
│   └── research_tools.py  # 5个@tool函数
│
├── data/                  # 数据目录 (自动创建)
│   └── vector_index/      # ChromaDB数据
│
├── main.py                # 主程序 (可选)
├── requirements.txt       # 依赖列表
├── .env.example           # 环境变量示例
├── .env                   # 你的配置 (不要上传!)
└── TUTORIAL.md            # 本教程
```

### 每个模块的作用

#### 1. services/model_factory.py (25行)

**作用**: 创建和管理API客户端

```python
# 核心代码
class ModelFactory:
    @classmethod
    def get_client(cls, provider="dashscope"):
        return OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
```

**为什么需要**: 统一管理API客户端,避免重复创建

#### 2. services/pdf_service.py (125行)

**作用**: 调用MinerU云服务解析PDF

**核心流程**:
```
提交PDF URL → 轮询解析状态 → 下载ZIP结果 → 提取markdown/表格/图片
```

#### 3. services/vision_service.py (32行)

**作用**: 用Qwen-VL理解图像

**使用场景**: 分析论文中的图表、公式

#### 4. services/embedding_service.py (22行)

**作用**: 把文本转换为向量

**为什么需要**: 向量数据库需要数字向量,不能直接存文本

#### 5. services/vector_store.py (115行)

**作用**: 存储和搜索向量

**核心功能**:
- `add_texts()`: 添加文档
- `search()`: 语义搜索
- `save()`: 保存 (自动)

### 数据流动过程

```
用户提问: "Transformer的创新点?"
    ↓
【1. 任务分解】PlannerAgent
    输入: "Transformer的创新点?"
    输出: ["理解架构", "分析attention", "对比RNN"]
    ↓
【2. 证据检索】RetrieverAgent
    输入: ["理解架构", "分析attention", "对比RNN"]
    过程:
        - embedding_service.embed("理解架构") → 向量
        - vector_store.search(向量) → 相关文本
    输出: 15条证据
    ↓
【3. 图像理解】CaptionAgent (如果有图)
    输入: "figure_1.jpg"
    过程:
        - vision_service.analyze(image, question)
    输出: "这张图展示了attention机制的计算过程..."
    ↓
【4. 推理生成】ReasonerAgent
    输入: 问题 + 证据 + 图像描述
    过程:
        - 构建prompt
        - 调用Qwen3模型
        - 解析JSON结果
    输出: {"answer": "...", "confidence": 0.87}
    ↓
【5. 质量检查】ReviewerAgent
    输入: 问题 + 答案 + 证据 + 置信度
    过程:
        - 规则检查 (长度、置信度、证据数量)
        - LLM检查 (完整性、逻辑性)
    输出: {"final_confidence": 0.85, "need_iterate": false}
    ↓
返回给用户
```

---

## 常见问题

### Q1: 为什么要用云API,不能本地部署吗?

**答**: 可以,但不推荐初学者这样做

**原因**:
- ❌ Qwen3-72B需要4张A100 GPU (成本>10万)
- ❌ 环境配置复杂 (CUDA、PyTorch、模型下载)
- ✅ 云API简单、便宜、稳定

**成本对比**:
- 本地部署: >10万元硬件 + 高电费
- 云API: 免费额度够测试,付费也很便宜 (0.001元/千token)

### Q2: PDF必须是公开URL吗?

**答**: 是的,MinerU云服务需要能访问的URL

**解决方案**:
1. 上传到GitHub Release
2. 使用临时文件托管 (如transfer.sh)
3. 自己搭建简单的文件服务器

### Q3: ChromaDB数据存在哪里?

**答**: `./data/vector_index/` 目录

**查看数据量**:
```python
from tools.research_tools import vector_service
print(f"当前向量数: {vector_service.collection.count()}")
```

**清空数据**:
```python
vector_service.reset()
```

### Q4: 如何调试错误?

**方法1: 打印变量**
```python
print(f"Debug: plan = {plan}")
```

**方法2: 使用try-except**
```python
try:
    result = process_research_paper(pdf_url)
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
```

**方法3: 检查API密钥**
```python
import os
print(f"API密钥存在: {bool(os.getenv('DASHSCOPE_API_KEY'))}")
```

### Q5: 置信度是什么意思?

**答**: 0-1之间的数字,表示AI对答案的"确信程度"

| 置信度 | 含义 | 处理建议 |
|-------|------|---------|
| 0.8-1.0 | 非常确定 | 可以直接使用 |
| 0.6-0.8 | 比较确定 | 建议验证 |
| <0.6 | 不太确定 | 需要人工检查 |

**计算依据**:
- 证据数量 (越多越好)
- 证据相关性 (越相关越好)
- LLM自我评估

---

## 学习路径

### 第1天: 环境准备和第一次运行
- ✅ 安装Python和依赖
- ✅ 获取API密钥
- ✅ 运行示例1 (解析PDF)
- ✅ 运行示例2 (搜索)

### 第2-3天: 理解核心概念
- ✅ 阅读"核心概念"章节
- ✅ 理解Multi-Agent架构
- ✅ 理解向量数据库原理
- ✅ 运行示例3 (完整流程)

### 第4-5天: 深入代码
- ✅ 阅读services/代码
- ✅ 理解每个Agent的作用
- ✅ 修改参数试试 (top_k, temperature)

### 第6-7天: 自己写代码
- ✅ 写一个简单的查询脚本
- ✅ 批量处理多篇论文
- ✅ 自定义Agent参数

---

## 进阶思路和扩展方向

学完基础教程后,你可以尝试以下进阶功能和扩展方向。

### 🚀 进阶功能 (提升系统能力)

#### 1. 批量处理多篇论文

**场景**: 分析某个研究方向的10篇相关论文

```python
from tools.research_tools import process_research_paper
import json

# 论文列表
papers = [
    "https://arxiv.org/pdf/1706.03762.pdf",  # Transformer
    "https://arxiv.org/pdf/1810.04805.pdf",  # BERT
    "https://arxiv.org/pdf/2005.14165.pdf",  # GPT-3
    # ... 更多论文
]

# 批量处理
results = []
for i, url in enumerate(papers, 1):
    print(f"\n📄 处理论文 {i}/{len(papers)}")
    try:
        result = process_research_paper(url)
        results.append(json.loads(result))
        print(f"✅ 成功: {url}")
    except Exception as e:
        print(f"❌ 失败: {e}")

# 统计分析
total_text = sum(r['text_length'] for r in results)
total_tables = sum(r['tables_count'] for r in results)
total_images = sum(r['images_count'] for r in results)

print(f"\n📊 批量处理统计:")
print(f"总文本量: {total_text:,} 字符")
print(f"总表格数: {total_tables} 个")
print(f"总图片数: {total_images} 个")
```

**改进点**:
- ✅ 添加进度条 (使用tqdm)
- ✅ 失败重试机制
- ✅ 保存中间结果

#### 2. 文献综述生成

**场景**: 基于多篇论文生成研究综述

```python
from agents.research_agents import ReasonerAgent
from tools.research_tools import search_documents

# 综述主题
topic = "Transformer架构在NLP中的应用"

# 1. 检索相关内容
print("🔍 检索相关文献...")
evidence_queries = [
    "Transformer基本原理",
    "Transformer在机器翻译中的应用",
    "Transformer在文本生成中的应用",
    "Transformer的改进变体"
]

all_evidence = []
for query in evidence_queries:
    results = search_documents(query, top_k=10)
    all_evidence.append({
        "task": query,
        "evidence": json.loads(results)
    })

# 2. 生成综述
print("\n📝 生成文献综述...")
reasoner = ReasonerAgent()
review = reasoner.reason(
    question=f"请生成关于'{topic}'的文献综述",
    evidence=all_evidence,
    require_citations=True
)

print(f"\n📄 综述内容:\n{review['answer']}")
print(f"\n📊 置信度: {review['confidence']:.2f}")
```

**扩展方向**:
- 📊 添加可视化 (时间线、引用网络)
- 📁 导出为Markdown/PDF
- 🔄 迭代优化 (基于ReviewerAgent反馈)

#### 3. 图表深度分析

**场景**: 提取论文中所有图表并分析

```python
from services import PDFService, VisionService
import zipfile
import io

# 解析PDF并获取图像
pdf_service = PDFService()
result = pdf_service.parse("https://arxiv.org/pdf/1706.03762.pdf")

# 分析每张图
vision_service = VisionService()
for i, image_info in enumerate(result['images'], 1):
    print(f"\n🖼️ 分析图片 {i}/{len(result['images'])}")

    # 假设图片已下载到本地
    image_path = f"./data/images/{image_info['path_in_zip']}"

    # 多角度分析
    questions = [
        "这张图展示了什么内容?",
        "图中的关键数据是什么?",
        "这张图支持什么结论?"
    ]

    for q in questions:
        answer = vision_service.analyze(image_path, q)
        print(f"  Q: {q}")
        print(f"  A: {answer}\n")
```

**改进方向**:
- 📊 图表类型识别 (折线图/柱状图/流程图)
- 🔢 数据提取 (OCR数值)
- 📈 趋势分析

#### 4. 自定义Agent开发

**场景**: 创建一个"相关工作推荐"Agent

```python
from services import ModelFactory
from tools.research_tools import vector_service

class RelatedWorkAgent:
    """相关工作推荐Agent"""

    def __init__(self, model_name="qwen-plus"):
        self.client = ModelFactory.get_client()
        self.model_name = model_name

    def recommend(self, current_paper_summary: str, top_k: int = 5):
        """推荐相关论文

        Args:
            current_paper_summary: 当前论文摘要
            top_k: 推荐数量
        """
        # 1. 提取关键概念
        prompt = f"""从以下论文摘要中提取3-5个核心研究主题:

摘要: {current_paper_summary}

请以JSON格式返回:
{{"keywords": ["主题1", "主题2", "主题3"]}}
"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )

        keywords_text = response.choices[0].message.content
        keywords = json.loads(keywords_text)['keywords']

        # 2. 检索相关文献
        recommendations = []
        for keyword in keywords:
            results = vector_service.search(keyword, top_k=3)
            recommendations.extend(results)

        # 3. 去重排序
        seen = set()
        unique_recs = []
        for rec in recommendations:
            text_hash = hash(rec['text'][:100])
            if text_hash not in seen:
                seen.add(text_hash)
                unique_recs.append(rec)

        return sorted(unique_recs, key=lambda x: x['score'])[:top_k]

# 使用示例
agent = RelatedWorkAgent()
summary = "本文提出了Transformer架构..."
recs = agent.recommend(summary, top_k=5)

print("📚 相关工作推荐:")
for i, rec in enumerate(recs, 1):
    print(f"{i}. {rec['text'][:200]}... (相关度: {rec['score']:.2f})")
```

### 🌟 扩展方向 (创新功能)

#### 扩展1: 研究空白探测

**概念**: 分析当前研究方向的未解决问题

**实现思路**:
```python
class ResearchGapAgent:
    """研究空白探测Agent"""

    def detect_gaps(self, papers: list, topic: str):
        """
        分析策略:
        1. 提取所有论文的局限性部分
        2. 提取所有"Future Work"部分
        3. 分析未被充分研究的子领域
        4. 生成研究机会报告
        """
        pass
```

**应用场景**:
- 📖 文献综述撰写
- 💡 研究选题
- 🎯 确定研究方向

#### 扩展2: 实验方法对比

**概念**: 自动提取和对比不同论文的实验设置

**实现思路**:
```python
class ExperimentComparisonAgent:
    """实验方法对比Agent"""

    def compare_experiments(self, papers: list):
        """
        对比维度:
        1. 数据集 (名称、规模、来源)
        2. 评估指标 (Accuracy、F1、BLEU等)
        3. 基线模型
        4. 实验环境 (硬件、超参数)

        输出:
        - 对比表格
        - 性能趋势图
        - 方法演进分析
        """
        pass
```

**应用场景**:
- 📊 实验设计参考
- 🏆 SOTA结果追踪
- 📈 性能基准建立

#### 扩展3: 引用网络分析

**概念**: 构建论文引用关系图谱

**实现思路**:
```python
class CitationNetworkAgent:
    """引用网络分析Agent"""

    def build_network(self, seed_paper: str, depth: int = 2):
        """
        构建步骤:
        1. 提取种子论文的引用列表
        2. 递归获取被引论文
        3. 构建引用图谱
        4. 计算重要性指标 (PageRank、中心性)

        可视化:
        - 引用关系图
        - 研究演进时间线
        - 核心论文识别
        """
        pass
```

**技术栈**:
- NetworkX (图分析)
- Plotly (交互可视化)
- Semantic Scholar API (引用数据)

#### 扩展4: 多语言支持

**概念**: 支持中英文混合分析

**实现要点**:
```python
# 1. 检测语言
from langdetect import detect

def detect_language(text):
    return detect(text)

# 2. 根据语言选择不同的提示词模板
PROMPTS = {
    "zh": "请基于以下证据回答问题...",
    "en": "Please answer the question based on the evidence..."
}

# 3. 翻译功能 (可选)
def translate_if_needed(text, target_lang="zh"):
    # 使用Qwen3翻译功能
    pass
```

#### 扩展5: 知识图谱构建

**概念**: 从论文中提取实体和关系

**实现示例**:
```python
class KnowledgeGraphAgent:
    """知识图谱构建Agent"""

    def extract_entities(self, text: str):
        """
        提取实体:
        - 模型名称 (BERT, GPT-3, Transformer)
        - 数据集 (ImageNet, COCO, SQuAD)
        - 评估指标 (Accuracy, F1-Score)
        - 研究机构 (OpenAI, Google, Meta)
        """
        prompt = f"""从以下文本中提取科研实体:

文本: {text}

请返回JSON:
{{
    "models": [...],
    "datasets": [...],
    "metrics": [...],
    "organizations": [...]
}}
"""
        # 调用LLM提取
        pass

    def extract_relations(self, text: str):
        """
        提取关系:
        - "模型A" 在 "数据集B" 上达到 "指标C"
        - "论文X" 改进了 "模型Y"
        - "方法A" 优于 "方法B"
        """
        pass
```

**应用**:
- 🔍 智能问答
- 📊 领域知识可视化
- 🔗 实体关联分析

### 🛠️ 工程优化方向

#### 优化1: 缓存机制

**问题**: 重复解析同一篇论文浪费时间和API额度

**解决方案**:
```python
import hashlib
import pickle
from pathlib import Path

class CacheManager:
    """解析结果缓存"""

    def __init__(self, cache_dir="./data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, pdf_url: str) -> str:
        return hashlib.md5(pdf_url.encode()).hexdigest()

    def get(self, pdf_url: str):
        cache_file = self.cache_dir / f"{self.get_cache_key(pdf_url)}.pkl"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None

    def set(self, pdf_url: str, data):
        cache_file = self.cache_dir / f"{self.get_cache_key(pdf_url)}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

# 使用
cache = CacheManager()
pdf_url = "https://arxiv.org/pdf/1706.03762.pdf"

result = cache.get(pdf_url)
if result is None:
    result = pdf_service.parse(pdf_url)
    cache.set(pdf_url, result)
```

#### 优化2: 异步处理

**问题**: 批量处理论文时串行太慢

**解决方案**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_paper_async(pdf_url: str):
    """异步处理单篇论文"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            process_research_paper,
            pdf_url
        )
    return result

async def batch_process(pdf_urls: list):
    """批量异步处理"""
    tasks = [process_paper_async(url) for url in pdf_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# 使用
urls = ["url1", "url2", "url3"]
results = asyncio.run(batch_process(urls))
```

#### 优化3: Web界面

**技术栈**: Gradio / Streamlit

```python
import gradio as gr

def research_interface(pdf_url, question):
    """简单的Web界面"""
    # 1. 解析PDF
    result = process_research_paper(pdf_url)

    # 2. 回答问题
    planner = PlannerAgent()
    plan = planner.plan(question)

    retriever = RetrieverAgent()
    evidence = retriever.retrieve(plan['sub_tasks'])

    reasoner = ReasonerAgent()
    answer = reasoner.reason(question, evidence)

    return answer['answer'], answer['confidence']

# 创建界面
demo = gr.Interface(
    fn=research_interface,
    inputs=[
        gr.Textbox(label="PDF URL"),
        gr.Textbox(label="研究问题")
    ],
    outputs=[
        gr.Textbox(label="答案"),
        gr.Number(label="置信度")
    ],
    title="SciResearcher - 科研文献分析助手"
)

demo.launch()
```

### 📚 学习资源推荐

#### 进阶阅读

1. **Multi-Agent系统**
   - Paper: "AutoGen: Enabling Next-Gen LLM Applications"
   - Book: "Multi-Agent Systems" by Gerhard Weiss

2. **RAG技术**
   - Paper: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
   - Tutorial: LangChain RAG官方教程

3. **科研应用**
   - Paper: "Scientific Discovery in the Age of AI"
   - Blog: Semantic Scholar技术博客

#### 开源项目参考

```
相似项目:
├── PaperQA - https://github.com/whitead/paper-qa
├── LlamaIndex - https://github.com/run-llama/llama_index
├── LangChain - https://github.com/langchain-ai/langchain
└── AutoGen - https://github.com/microsoft/autogen

差异化:
✅ SciResearcher: 专注科研、多模态、轻量级
```

---

## 下一步

学完这个教程和进阶内容,你应该能够:

✅ 理解SciResearcher的整体架构
✅ 独立运行论文分析流程
✅ 修改参数和配置
✅ 调试简单的错误
✅ 扩展新功能
✅ 优化系统性能

**继续学习**:
- 📖 阅读 smolagents官方文档
- 📖 阅读 Qwen3模型文档
- 📖 阅读 ChromaDB文档
- 🔧 实现一个自定义Agent
- 🌟 尝试一个扩展方向

**参考资料**:
- Smolagents: https://huggingface.co/docs/smolagents
- Qwen3: https://help.aliyun.com/zh/dashscope/
- ChromaDB: https://docs.trychroma.com/
- MinerU: https://mineru.net/docs

---

## 附录: 快速命令参考

```bash
# 环境准备
python -m venv venv
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# 配置
cp .env.example .env
nano .env

# 运行测试
python test_agent.py

# 查看向量数
python -c "from tools.research_tools import vector_service; print(vector_service.collection.count())"

# 清空向量库
python -c "from tools.research_tools import vector_service; vector_service.reset()"
```

---

**🎉 恭喜你完成了初学者教程!**

如果有问题,欢迎查看:
- 完整技术文档: `claudedocs/refactoring_summary.md`
- 向量数据库迁移: `claudedocs/vector_db_migration.md`
