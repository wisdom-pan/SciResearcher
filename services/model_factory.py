"""
模型客户端工厂
"""
import os
from openai import OpenAI

class ModelFactory:
    """OpenAI 兼容客户端工厂"""

    _clients = {}

    @classmethod
    def get_client(cls, provider: str = "modelscope") -> OpenAI:
        """获取客户端实例"""
        if provider not in cls._clients:
            if provider == "modelscope":
                cls._clients[provider] = OpenAI(
                    api_key=os.getenv("MODELSCOPE_API_KEY"),
                    base_url=os.getenv("MODELSCOPE_BASE_URL")
                )
            elif provider == "dashscope":
                # 兼容旧的dashscope配置
                cls._clients[provider] = OpenAI(
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        return cls._clients[provider]
