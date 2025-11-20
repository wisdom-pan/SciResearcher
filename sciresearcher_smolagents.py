"""
基于 smolagents 的 SciResearcher 主系统
使用 Qwen3 系列模型 + MinerU2.5
"""
import os
from pathlib import Path
from smolagents import CodeAgent, ToolCallingAgent, HfApiModel, LiteLLMModel
from tools.smolagents_tools import (
    parse_pdf,
    index_text,
    search_knowledge,
    understand_image,
    process_and_index_pdf
)

class SciResearcherAgent:
    """
    基于 smolagents 的科研文献理解系统

    架构:
    - 使用 smolagents 的 Agent 框架
    - Qwen3 系列模型作为LLM
    - MinerU2.5 进行PDF解析
    - 向量检索增强生成(RAG)
    """

    def __init__(self, model_name: str = "qwen-plus", use_tool_calling: bool = True):
        """
        初始化 SciResearcher Agent

        Args:
            model_name: Qwen模型名称 (qwen-plus, qwen-turbo, qwen-max等)
            use_tool_calling: 是否使用ToolCallingAgent (推荐)
        """
        print("=" * 70)
        print("SciResearcher - 基于 smolagents + Qwen3 + MinerU2.5")
        print("=" * 70)

        # 检查API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError(
                "请设置环境变量 DASHSCOPE_API_KEY\n"
                "获取地址: https://dashscope.console.aliyun.com/apiKey"
            )

        print(f"\n初始化模型: {model_name}")

        # 初始化Qwen模型 (通过LiteLLM支持阿里云百炼API)
        self.model = LiteLLMModel(
            model_id=f"openai/{model_name}",  # LiteLLM格式
            api_key=api_key,
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 准备工具列表
        tools = [
            process_and_index_pdf,
            search_knowledge,
            understand_image,
            parse_pdf,
            index_text
        ]

        print(f"加载工具: {len(tools)} 个")

        # 创建Agent
        if use_tool_calling:
            # 使用ToolCallingAgent (更智能)
            self.agent = ToolCallingAgent(
                tools=tools,
                model=self.model,
                max_steps=10
            )
            print("✓ 使用 ToolCallingAgent")
        else:
            # 使用CodeAgent (更灵活)
            self.agent = CodeAgent(
                tools=tools,
                model=self.model,
                max_steps=10
            )
            print("✓ 使用 CodeAgent")

        print("\n系统初始化完成!")
        print("=" * 70)

    def process_pdf(self, pdf_path: str) -> str:
        """
        处理PDF文件

        Args:
            pdf_path: PDF文件路径

        Returns:
            处理结果
        """
        task = f"""
请使用 process_and_index_pdf 工具处理以下PDF文件，完成解析和索引:
PDF路径: {pdf_path}

请告诉我:
1. 提取了多少文字
2. 找到了多少图片
3. 找到了多少表格和公式
4. 索引状态
"""
        return self.agent.run(task)

    def answer_question(self, question: str) -> str:
        """
        回答关于已索引文档的问题

        Args:
            question: 用户问题

        Returns:
            答案
        """
        task = f"""
请回答以下科研问题，要求:

问题: {question}

步骤:
1. 使用 search_knowledge 工具检索相关文献内容
2. 分析检索到的证据
3. 生成详细答案，必须包含:
   - 基于证据的回答
   - 明确标注引用的证据来源 [证据1] [证据2] 等
   - 给出置信度评分(0-1)
   - 如果证据不足，明确说明

请开始回答。
"""
        return self.agent.run(task)

    def analyze_figures(self, question: str, image_paths: list) -> str:
        """
        分析论文中的图表

        Args:
            question: 关于图表的问题
            image_paths: 图片路径列表

        Returns:
            分析结果
        """
        images_str = "\n".join([f"- {path}" for path in image_paths])

        task = f"""
请分析以下图表并回答问题:

问题: {question}

图表路径:
{images_str}

对每张图使用 understand_image 工具进行分析，然后综合回答问题。
"""
        return self.agent.run(task)

    def comprehensive_analysis(self, pdf_path: str, question: str) -> str:
        """
        完整分析流程: 处理PDF + 回答问题

        Args:
            pdf_path: PDF路径
            question: 问题

        Returns:
            完整分析结果
        """
        task = f"""
请完成以下科研文献分析任务:

1. 处理PDF文件: {pdf_path}
   使用 process_and_index_pdf 工具

2. 回答问题: {question}
   使用 search_knowledge 工具检索相关内容

3. 如果发现有相关图表，使用 understand_image 工具分析

4. 生成完整报告，包括:
   - 文献基本信息
   - 问题答案 (带引用)
   - 图表分析 (如有)
   - 置信度评分

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
        help="PDF文件路径"
    )
    parser.add_argument(
        "--question",
        type=str,
        help="要回答的问题"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen-plus",
        help="Qwen模型名称 (qwen-plus, qwen-turbo, qwen-max)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="tool-calling",
        choices=["tool-calling", "code"],
        help="Agent模式: tool-calling 或 code"
    )

    args = parser.parse_args()

    # 创建Agent
    agent = SciResearcherAgent(
        model_name=args.model,
        use_tool_calling=(args.mode == "tool-calling")
    )

    # 完整分析
    if args.pdf and args.question:
        print(f"\n执行完整分析...")
        result = agent.comprehensive_analysis(args.pdf, args.question)
        print("\n" + "=" * 70)
        print("分析结果:")
        print("=" * 70)
        print(result)

    # 只处理PDF
    elif args.pdf:
        print(f"\n处理PDF: {args.pdf}")
        result = agent.process_pdf(args.pdf)
        print("\n" + "=" * 70)
        print("处理结果:")
        print("=" * 70)
        print(result)

    # 只回答问题
    elif args.question:
        print(f"\n回答问题: {args.question}")
        result = agent.answer_question(args.question)
        print("\n" + "=" * 70)
        print("答案:")
        print("=" * 70)
        print(result)

    # 交互模式
    else:
        print("\n进入交互模式")
        print("=" * 70)

        while True:
            print("\n请选择操作:")
            print("1. 处理PDF文件")
            print("2. 回答问题")
            print("3. 完整分析 (PDF + 问题)")
            print("4. 退出")

            choice = input("\n请输入选项 (1-4): ").strip()

            if choice == "1":
                pdf_path = input("请输入PDF路径: ").strip()
                if pdf_path:
                    result = agent.process_pdf(pdf_path)
                    print(f"\n结果:\n{result}")

            elif choice == "2":
                question = input("请输入问题: ").strip()
                if question:
                    result = agent.answer_question(question)
                    print(f"\n答案:\n{result}")

            elif choice == "3":
                pdf_path = input("请输入PDF路径: ").strip()
                question = input("请输入问题: ").strip()
                if pdf_path and question:
                    result = agent.comprehensive_analysis(pdf_path, question)
                    print(f"\n分析结果:\n{result}")

            elif choice == "4":
                print("再见!")
                break

            else:
                print("无效选项")


if __name__ == "__main__":
    main()
