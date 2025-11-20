"""
Research Agents - 5个专门的研究Agent
基于 smolagents 框架实现
"""
from typing import List, Dict, Any
import json
from pathlib import Path

# 从 tools 导入服务
import sys
sys.path.append(str(Path(__file__).parent.parent))
from tools.research_tools import (
    embedding_service,
    vector_service,
    vision_service
)
from services import ModelFactory

# ============================================================================
# Agent 1: Planner - 任务分解Agent
# ============================================================================

class PlannerAgent:
    """任务分解Agent - 将复杂问题分解为子任务"""

    def __init__(self, model_name: str = "qwen-plus"):
        self.model_name = model_name
        self.client = ModelFactory.get_client("dashscope")

    def plan(self, question: str) -> Dict[str, Any]:
        """分解任务

        Args:
            question: 研究问题

        Returns:
            {
                "sub_tasks": List[str],  # 子任务列表
                "strategy": str,         # 执行策略
                "priority": List[int]    # 优先级
            }
        """
        prompt = f"""你是一个研究任务规划专家。请将以下研究问题分解为可执行的子任务。

研究问题: {question}

请按以下格式输出:
1. 子任务列表 (3-5个具体的、可执行的任务)
2. 执行策略 (parallel/sequential)
3. 优先级排序

输出JSON格式:
{{
    "sub_tasks": ["任务1", "任务2", ...],
    "strategy": "parallel或sequential",
    "priority": [1, 2, 3, ...]
}}
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        result_text = response.choices[0].message.content

        # 提取JSON
        try:
            # 查找JSON块
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            if start != -1 and end > start:
                result = json.loads(result_text[start:end])
            else:
                # 降级处理
                result = {
                    "sub_tasks": [question],
                    "strategy": "sequential",
                    "priority": [1]
                }
        except:
            result = {
                "sub_tasks": [question],
                "strategy": "sequential",
                "priority": [1]
            }

        return result


# ============================================================================
# Agent 2: Retriever - 多模态检索Agent
# ============================================================================

class RetrieverAgent:
    """多模态检索Agent - 基于子任务检索证据"""

    def __init__(self):
        self.vector_service = vector_service
        self.embedding_service = embedding_service

    def retrieve(self, sub_tasks: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """检索证据

        Args:
            sub_tasks: 子任务列表
            top_k: 每个任务返回的结果数

        Returns:
            List[{
                "task": str,
                "evidence": List[{
                    "text": str,
                    "score": float,
                    "metadata": dict
                }]
            }]
        """
        all_evidence = []

        for task in sub_tasks:
            # 语义搜索
            results = self.vector_service.search(task, top_k)

            all_evidence.append({
                "task": task,
                "evidence": results,
                "evidence_count": len(results)
            })

        return all_evidence


# ============================================================================
# Agent 3: Caption Agent - 图像理解Agent
# ============================================================================

class CaptionAgent:
    """图像理解Agent - 理解图表和图像"""

    def __init__(self, model_name: str = "qwen-vl-max"):
        self.vision_service = vision_service
        self.model_name = model_name

    def caption(self, image_path: str, task: str = None) -> Dict[str, Any]:
        """图像理解

        Args:
            image_path: 图像路径
            task: 特定任务描述 (可选)

        Returns:
            {
                "description": str,  # 图像描述
                "key_findings": List[str],  # 关键发现
                "metadata": dict
            }
        """
        # 构建问题
        if task:
            question = f"请根据以下任务分析这张图: {task}。请详细描述图中的关键信息。"
        else:
            question = "请详细描述这张图表的内容,包括: 1)图表类型 2)主要数据 3)关键结论"

        # 调用视觉模型
        description = self.vision_service.process(image_path, question)

        # 解析关键发现 (简单实现)
        key_findings = [
            line.strip() for line in description.split('\n')
            if line.strip() and (
                line.strip().startswith('-') or
                line.strip().startswith('•') or
                line.strip()[0].isdigit()
            )
        ]

        return {
            "description": description,
            "key_findings": key_findings[:5],  # 最多5个关键发现
            "metadata": {
                "model": self.model_name,
                "image_path": image_path
            }
        }


# ============================================================================
# Agent 4: Reasoner - 推理生成Agent
# ============================================================================

class ReasonerAgent:
    """推理生成Agent - 基于证据生成答案"""

    def __init__(self, model_name: str = "qwen-plus"):
        self.model_name = model_name
        self.client = ModelFactory.get_client("dashscope")

    def reason(
        self,
        question: str,
        evidence: List[Dict[str, Any]],
        require_citations: bool = True
    ) -> Dict[str, Any]:
        """推理生成答案

        Args:
            question: 原始问题
            evidence: 检索到的证据
            require_citations: 是否需要引用

        Returns:
            {
                "answer": str,
                "confidence": float,
                "citations": List[str]
            }
        """
        # 构建证据上下文
        evidence_text = self._format_evidence(evidence)

        # 构建提示词
        prompt = f"""你是一个科研文献分析专家。请基于提供的证据回答问题。

问题: {question}

证据:
{evidence_text}

要求:
1. 基于证据给出准确的答案
2. 如果证据不足,明确指出
3. 给出置信度评分 (0-1)
{"4. 标注引用来源" if require_citations else ""}

输出JSON格式:
{{
    "answer": "详细答案",
    "confidence": 0.0-1.0,
    "reasoning": "推理过程",
    "citations": ["引用1", "引用2", ...]
}}
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        result_text = response.choices[0].message.content

        # 解析结果
        try:
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            if start != -1 and end > start:
                result = json.loads(result_text[start:end])
            else:
                result = {
                    "answer": result_text,
                    "confidence": 0.5,
                    "reasoning": "无法解析推理过程",
                    "citations": []
                }
        except:
            result = {
                "answer": result_text,
                "confidence": 0.5,
                "reasoning": "解析失败",
                "citations": []
            }

        return result

    def _format_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        """格式化证据"""
        formatted = []
        for i, item in enumerate(evidence, 1):
            task = item.get("task", "")
            evidences = item.get("evidence", [])

            formatted.append(f"\n### 子任务{i}: {task}")
            for j, ev in enumerate(evidences[:3], 1):  # 每个任务最多3条证据
                text = ev.get("text", "")
                score = ev.get("score", 0)
                formatted.append(f"{j}. [相关度: {score:.2f}] {text[:300]}...")

        return "\n".join(formatted)


# ============================================================================
# Agent 5: Reviewer - 自我校验Agent
# ============================================================================

class ReviewerAgent:
    """自我校验Agent - 检查答案质量并决定是否需要迭代"""

    def __init__(self, model_name: str = "qwen-plus"):
        self.model_name = model_name
        self.client = ModelFactory.get_client("dashscope")

    def review(
        self,
        question: str,
        answer: str,
        evidence: List[Dict[str, Any]],
        confidence: float
    ) -> Dict[str, Any]:
        """校验答案

        Args:
            question: 原始问题
            answer: 生成的答案
            evidence: 使用的证据
            confidence: 置信度

        Returns:
            {
                "final_answer": str,
                "final_confidence": float,
                "need_iterate": bool,
                "issues": List[str],
                "suggestions": List[str]
            }
        """
        # 规则校验
        rule_check = self._rule_based_check(answer, evidence, confidence)

        # LLM 校验
        llm_check = self._llm_based_check(question, answer, evidence)

        # 综合判断
        need_iterate = rule_check["need_iterate"] or llm_check["need_iterate"]
        issues = rule_check["issues"] + llm_check["issues"]

        return {
            "final_answer": answer,
            "final_confidence": min(confidence, llm_check.get("confidence", confidence)),
            "need_iterate": need_iterate,
            "issues": issues,
            "suggestions": llm_check.get("suggestions", [])
        }

    def _rule_based_check(
        self,
        answer: str,
        evidence: List[Dict[str, Any]],
        confidence: float
    ) -> Dict[str, Any]:
        """基于规则的校验"""
        issues = []
        need_iterate = False

        # 规则1: 答案长度检查
        if len(answer) < 50:
            issues.append("答案过短,可能不够详细")
            need_iterate = True

        # 规则2: 置信度检查
        if confidence < 0.6:
            issues.append(f"置信度过低 ({confidence:.2f})")
            need_iterate = True

        # 规则3: 证据充分性检查
        total_evidence = sum(len(e.get("evidence", [])) for e in evidence)
        if total_evidence < 3:
            issues.append(f"证据不足 (仅{total_evidence}条)")
            need_iterate = True

        # 规则4: 关键词检查
        uncertainty_keywords = ["不确定", "可能", "也许", "不清楚"]
        if any(kw in answer for kw in uncertainty_keywords):
            issues.append("答案包含不确定表述")

        return {
            "need_iterate": need_iterate,
            "issues": issues
        }

    def _llm_based_check(
        self,
        question: str,
        answer: str,
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """基于LLM的校验"""
        prompt = f"""你是一个科研文献质量评审专家。请评估以下答案的质量。

问题: {question}

答案: {answer}

证据数量: {sum(len(e.get("evidence", [])) for e in evidence)}

请评估:
1. 答案是否完整回答了问题
2. 答案是否有足够证据支持
3. 答案是否存在逻辑问题
4. 置信度评分 (0-1)
5. 是否需要重新生成

输出JSON:
{{
    "need_iterate": true/false,
    "confidence": 0.0-1.0,
    "issues": ["问题1", "问题2", ...],
    "suggestions": ["建议1", "建议2", ...]
}}
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        result_text = response.choices[0].message.content

        try:
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            if start != -1 and end > start:
                result = json.loads(result_text[start:end])
            else:
                result = {
                    "need_iterate": False,
                    "confidence": 0.7,
                    "issues": [],
                    "suggestions": []
                }
        except:
            result = {
                "need_iterate": False,
                "confidence": 0.7,
                "issues": [],
                "suggestions": []
            }

        return result


# ============================================================================
# 导出所有Agent
# ============================================================================

__all__ = [
    'PlannerAgent',
    'RetrieverAgent',
    'CaptionAgent',
    'ReasonerAgent',
    'ReviewerAgent'
]
