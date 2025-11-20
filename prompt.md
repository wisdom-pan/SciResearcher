## 背景

SciResearcher：基于Muti-Agent 协作的科研文献深度理解框架
参赛类别：科研框架（Scientific Framework）  
项目定位：首个基于 smolagents 与 Qwen3  系列模型、Mineru2.5 的科研文献研究框架，一个轻量、开源、可验证的科研 Agent 协作框架——让每一次 AI 回答经得起推敲
一、项目背景
🔬 科研工作者的现实困境
- 信息过载：arXiv 每日新增 200+ 论文，人工阅读效率低下；
- 理解深度比较低：现有工具（如 ChatPDF、ChatPaper等）仅支持摘要/关键词检索，无法回答“方法对比”“结果归因”“局限性分析”等高阶科研问题；
- AI 问答幻觉比较高：通用 RAG 系统常无引用、虚构结论，导致科研误判风险；
- 多模态信息处理比较片面：图表、公式、表格等关键证据未被系统利用——而超 60% 的科研结论依赖图表支撑。
  
当前开源项目问题：
- 单点工具（如 MinerU 解析、LlamaIndex 检索、RAG检索等）  
- 通用 Agent 框架（如 AutoGen、LangGraph），缺乏科研场景特化设计  
- 封闭商业系统（如 Scite、Consensus），定制化、很难扩展
二、项目目标
维度
MVP 目标
拓展思路
功能性
- 实现 Planning agent+4个sub agent 协作进行处理任务
- 支持 PDF 多模态解析 + 图像理解
- 输出带引用、置信度的答案
- mcp

- 支持多文档综述 
- 实验设计建议
- idea，研究空白探测
- Hugging Face daily paper支持
- 每种agent tool封装为mcp

技术实现
- Qwen3 家族模型
- smolagents 框架mvp实现
- 支持SFT、 LoRA 、GRPO微调
- vllm、sglang本地部署
三、技术方案
 核心思想：科研 Agent 范式
- Verifiable（可验证）：强制引用 + 置信度 + 自我校验  
- Retrieval-Augmented（检索增强）：Qwen3-Embedding + 多模态混合检索  
- Agent-Collaborative（Agent 协作）：smolagents 多智能体协同  
- Iterative：Reviewer → Retriever 迭代  
Agent 设计
[图片]

Agent
职责
输入/输出 Schema
技术实现
Planner
任务分解
Input: {question}
Output: {sub_tasks: List[str]}
LLM Prompt based

Retriever
多模态检索
Input: {sub_tasks}
Output: {evidence: List[Evidence]}
• Qwen3-Embedding +vector db
Caption Agent
图像理解
Input: {image_path, task}
Output: {description: str}
Qwen3-VL+MinerU

Reasoner
推理生成
Input: {question, evidence}
Output: {answer, confidence}
VL系列模型
Reviewer
自我校验
Input: {answer, evidence}
Output: {final_answer, confidence, need_iterate}
Rule base+llm judge
参考
https://github.com/huggingface/smolagents  
https://modelscope.cn/studios/ms-agent/DocResearch  
https://github.com/opendatalab/MinerU  

结合赛题要求：赛题一：AI+科研创新赛道

主题： “构建开源科研生态，加速科学发现”
参赛要求：
参赛者需要开发并开源具有科研价值的AI模型、应用或框架，重点关注：



科研模型：针对特定科研领域的创新AI模型（如分子发现、天体物理、气候预测等）

科研应用：基于AI技术的科研工具或平台（如文献分析、实验设计、数据可视化等）

科研框架：支持科研工作流的开源框架（如AutoML for Science、实验管理系统等）


技术要求：



必须在魔搭社区发布开源项目，包含完整代码、文档和使用示例

提供可复现的实验结果和评估基准

需要有实际科研场景的应用验证
赛题要求：赛题一：AI+科研创新赛道

开源项目代码包（含模型、工具或框架）

完整技术文档（安装指南、API说明、使用示例）

可复现的实验报告（含数据集说明、训练流程、评估指标）

应用验证案例（如在真实科研任务中的使用场景演示）

附带视频或图文说明，展示其在具体科研场景中的应用价值（如预测分子性质、分析天文图像等）

## 期望
从要给学习者讲清楚这个赛事怎么做的教程 ，从没有接触过这个比赛的人的角度、晓攀你这边觉得他们需要什么信息和材料，连串讲清楚这个事情，图文或者视频都可以