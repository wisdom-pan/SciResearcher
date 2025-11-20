"""
配置加载模块
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """配置管理类"""

    def __init__(self, config_path: str = None):
        """初始化配置

        Args:
            config_path: 配置文件路径,默认为 config/config.yaml
        """
        # 加载环境变量
        load_dotenv()

        # 确定配置文件路径
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        # 加载YAML配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # 替换环境变量
        self._replace_env_vars(self._config)

    def _replace_env_vars(self, obj: Any) -> Any:
        """递归替换配置中的环境变量

        Args:
            obj: 配置对象
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._replace_env_vars(value)
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            # 提取环境变量名
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj

    def get(self, path: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            path: 配置路径,用.分隔,如 'api.models.planner'
            default: 默认值

        Returns:
            配置值
        """
        keys = path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config

    @property
    def api_key(self) -> str:
        """获取API密钥"""
        return self.get('api.api_key')

    @property
    def api_base_url(self) -> str:
        """获取API基础URL"""
        return self.get('api.base_url')

    @property
    def planner_model(self) -> str:
        """获取Planner模型名"""
        return self.get('api.models.planner', 'qwen-plus')

    @property
    def reasoner_model(self) -> str:
        """获取Reasoner模型名"""
        return self.get('api.models.reasoner', 'qwen-plus')

    @property
    def reviewer_model(self) -> str:
        """获取Reviewer模型名"""
        return self.get('api.models.reviewer', 'qwen-turbo')

    @property
    def embedding_model(self) -> str:
        """获取Embedding模型名"""
        return self.get('api.models.embedding', 'text-embedding-v3')

    @property
    def vision_model(self) -> str:
        """获取Vision模型名"""
        return self.get('api.models.vision', 'qwen-vl-max')

# 全局配置实例
_config_instance = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
