"""
SciResearcher - 基于 smolagents 框架的科研文献理解系统
完全基于 API 实现，架构解耦

架构:
- smolagents: Multi-Agent 框架
- Qwen3 系列: LLM (qwen-plus, qwen-turbo)
- Qwen3 Embedding: 向量化 (text-embedding-v3)
- Qwen-VL: 视觉理解 (qwen-vl-max)
- MinerU API: PDF 解析
"""
import os
import sys
from pathlib import Path
from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel

# 添加工具路径
sys.path.append(str(Path(__file__).parent))

from tools.research_tools import (
    parse_pdf_with_mineru,
    index_documents,
    search_documents,
    analyze_image,
    process_research_paper
)


class SciResearcher:
    """
    SciResearcher 主系统

    基于 smolagents 的 Multi-Agent 科研文献理解框架
    """

    def __init__(
        self,
        model_name: str = "qwen-plus",
        agent_type: str = "tool-calling",
        max_steps: int = 15
    ):
        """
        初始化 SciResearcher

        Args:
            model_name: Qwen 模型名称 (qwen-plus, qwen-turbo, qwen-max)
            agent_type: Agent 类型 ("tool-calling" 或 "code")
            max_steps: 最大执行步数
        """
        print("=" * 80)
        print("SciResearcher - 科研文献深度理解框架")
        print("基于 smolagents + Qwen3 + MinerU API")
        print("=" * 80)

        # 检查 API 密钥
        self._check_api_keys()

        # 初始化 Qwen3 模型
        print(f"\n[1/3] 初始化 Qwen3 模型: {model_name}")
        self.model = LiteLLMModel(
            model_id=f"openai/{model_name}",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        print("✓ Qwen3 模型初始化完成")

        # 准备工具集
        print(f"\n[2/3] 加载研究工具")
        self.tools = [
            process_research_paper,    # 综合处理工具
            parse_pdf_with_mineru,     # PDF 解析
            index_documents,           # 文本索引
            search_documents,          # 语义搜索
            analyze_image             # 图像理解
        ]
        print(f"✓ 已加载 {len(self.tools)} 个工具")

        # 创建 Agent
        print(f"\n[3/3] 创建 Agent (类型: {agent_type})")
        if agent_type == "tool-calling":
            self.agent = ToolCallingAgent(
                tools=self.tools,
                model=self.model,
                max_steps=max_steps,
                verbosity_level=1
            )
        else:
            self.agent = CodeAgent(
                tools=self.tools,
                model=self.model,
                max_steps=max_steps,
                verbosity_level=1
            )
        print(f"✓ {agent_type.title()} Agent 初始化完成")

        print("\n" + "=" * 80)
        print("系统初始化完成! 🎉")
        print("=" * 80)

    def _check_api_keys(self):
        """检查必需的 API 密钥"""
        required_keys = {
            "DASHSCOPE_API_KEY": "阿里云百炼 API (用于 Qwen3 系列模型)"
        }

        optional_keys = {
            "MINERU_API_KEY": "MinerU API (用于 PDF 解析, 可选)"
        }

        missing_required = []
        for key, description in required_keys.items():
            if not os.getenv(key):
                missing_required.append(f"  - {key}: {description}")

        if missing_required:
            print("\n⚠️  缺少必需的 API 密钥:")
            print("\n".join(missing_required))
            print("\n请设置环境变量或在 .env 文件中配置")
            raise ValueError("缺少必需的 API 密钥")

        # 显示可选密钥状态
        for key, description in optional_keys.items():
            if os.getenv(key):
                print(f"✓ {key} 已配置")

    def process_pdf(self, pdf_path: str) -> str:
        """
        处理 PDF 文件

        Args:
            pdf_path: PDF 文件路径

        Returns:
            处理结果
        """
        task = f"""
请使用 process_research_paper 工具处理以下 PDF 文件:

PDF 路径: {pdf_path}

任务:
1. 使用 MinerU API 解析 PDF，提取文字、图片、表格、公式
2. 将提取的文本分块并索引到向量数据库
3. 返回处理摘要

请开始处理。
"""
        return self.agent.run(task)

    def answer_question(self, question: str, require_citations: bool = True) -> str:
        """
        回答科研问题

        Args:
            question: 用户问题
            require_citations: 是否要求引用证据

        Returns:
            答案
        """
        citations_requirement = """
- 必须明确标注引用来源，格式为 [证据1] [证据2]
- 给出置信度评分 (0-1)
- 说明推理过程
""" if require_citations else ""

        task = f"""
请回答以下科研问题:

问题: {question}

要求:
1. 使用 search_documents 工具检索相关文献内容 (top_k=5)
2. 分析检索到的证据
3. 生成详细答案
{citations_requirement}
4. 如果证据不足，明确说明并建议补充信息

请开始回答。
"""
        return self.agent.run(task)

    def analyze_figures(
        self,
        image_paths: list,
        question: str = "请分析这些图表并总结关键信息"
    ) -> str:
        """
        分析论文图表

        Args:
            image_paths: 图片路径列表
            question: 分析问题

        Returns:
            分析结果
        """
        images_list = "\n".join([f"  - {path}" for path in image_paths])

        task = f"""
请分析以下科研论文图表:

图表路径:
{images_list}

分析问题: {question}

要求:
1. 使用 analyze_image 工具逐个分析每张图表
2. 提取关键信息和数据
3. 综合所有图表给出结论

请开始分析。
"""
        return self.agent.run(task)

    def comprehensive_research(
        self,
        pdf_path: str,
        questions: list
    ) -> str:
        """
        完整的科研分析流程

        Args:
            pdf_path: PDF 文件路径
            questions: 问题列表

        Returns:
            完整分析报告
        """
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

        task = f"""
请完成以下科研文献的完整分析:

PDF 文件: {pdf_path}

研究问题:
{questions_text}

完整流程:
1. 使用 process_research_paper 处理 PDF
2. 对每个问题使用 search_documents 检索相关内容
3. 如果处理结果中包含图片路径，使用 analyze_image 分析关键图表
4. 生成完整研究报告，包含:
   - 文献基本信息
   - 每个问题的详细答案 (带引用和置信度)
   - 图表分析结果
   - 总结和结论

请开始分析。
"""
        return self.agent.run(task)

    def multi_paper_synthesis(
        self,
        pdf_paths: list,
        research_question: str
    ) -> str:
        """
        多文档综合分析

        Args:
            pdf_paths: PDF 文件路径列表
            research_question: 研究问题

        Returns:
            综合分析结果
        """
        pdfs_list = "\n".join([f"{i+1}. {path}" for i, path in enumerate(pdf_paths)])

        task = f"""
请进行多篇论文的综合分析:

论文列表:
{pdfs_list}

研究问题: {research_question}

任务:
1. 使用 process_research_paper 处理每篇 PDF
2. 使用 search_documents 检索所有论文中与问题相关的内容
3. 对比分析不同论文的观点和方法
4. 生成综合报告，包含:
   - 各论文的主要观点
   - 共识与分歧
   - 研究趋势
   - 综合结论

请开始分析。
"""
        return self.agent.run(task)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="SciResearcher - 基于 smolagents 的科研文献理解系统"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="PDF 文件路径"
    )
    parser.add_argument(
        "--question",
        type=str,
        help="要回答的问题"
    )
    parser.add_argument(
        "--images",
        type=str,
        nargs="+",
        help="图片路径列表"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen-plus",
        choices=["qwen-plus", "qwen-turbo", "qwen-max"],
        help="Qwen 模型名称"
    )
    parser.add_argument(
        "--agent-type",
        type=str,
        default="tool-calling",
        choices=["tool-calling", "code"],
        help="Agent 类型"
    )

    args = parser.parse_args()

    try:
        # 创建系统
        researcher = SciResearcher(
            model_name=args.model,
            agent_type=args.agent_type
        )

        # 处理 PDF
        if args.pdf and not args.question:
            print("\n" + "=" * 80)
            print("处理 PDF 文件")
            print("=" * 80)
            result = researcher.process_pdf(args.pdf)
            print(f"\n{result}")

        # 回答问题
        elif args.question and not args.pdf:
            print("\n" + "=" * 80)
            print("回答问题")
            print("=" * 80)
            result = researcher.answer_question(args.question)
            print(f"\n{result}")

        # 完整分析
        elif args.pdf and args.question:
            print("\n" + "=" * 80)
            print("完整研究分析")
            print("=" * 80)
            result = researcher.comprehensive_research(
                args.pdf,
                [args.question]
            )
            print(f"\n{result}")

        # 图表分析
        elif args.images:
            print("\n" + "=" * 80)
            print("图表分析")
            print("=" * 80)
            question = args.question or "请分析这些图表"
            result = researcher.analyze_figures(args.images, question)
            print(f"\n{result}")

        # 交互模式
        else:
            interactive_mode(researcher)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        sys.exit(1)


def interactive_mode(researcher: SciResearcher):
    """交互模式"""
    print("\n" + "=" * 80)
    print("交互模式")
    print("=" * 80)

    while True:
        print("\n请选择操作:")
        print("1. 处理 PDF 文件")
        print("2. 回答问题")
        print("3. 分析图表")
        print("4. 完整研究分析")
        print("5. 退出")

        choice = input("\n选择 (1-5): ").strip()

        if choice == "1":
            pdf_path = input("PDF 路径: ").strip()
            if pdf_path:
                result = researcher.process_pdf(pdf_path)
                print(f"\n结果:\n{result}")

        elif choice == "2":
            question = input("问题: ").strip()
            if question:
                result = researcher.answer_question(question)
                print(f"\n答案:\n{result}")

        elif choice == "3":
            images_input = input("图片路径 (用空格分隔): ").strip()
            question = input("分析问题 (可选): ").strip()

            if images_input:
                image_paths = images_input.split()
                result = researcher.analyze_figures(
                    image_paths,
                    question or "请分析这些图表"
                )
                print(f"\n分析:\n{result}")

        elif choice == "4":
            pdf_path = input("PDF 路径: ").strip()
            questions_input = input("问题 (用分号分隔): ").strip()

            if pdf_path and questions_input:
                questions = [q.strip() for q in questions_input.split(';')]
                result = researcher.comprehensive_research(pdf_path, questions)
                print(f"\n研究报告:\n{result}")

        elif choice == "5":
            print("\n再见! 👋")
            break

        else:
            print("无效选择")


if __name__ == "__main__":
    main()
