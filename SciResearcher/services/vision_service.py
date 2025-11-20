"""
视觉理解服务 (Qwen-VL)
"""
import base64
from .model_factory import ModelFactory

class VisionService:
    """Qwen-VL 视觉模型服务"""

    def __init__(self, model_name: str = "qwen-vl-max"):
        self.model_name = model_name
        self.client = ModelFactory.get_client()

    def analyze(self, image_path: str, question: str, temperature: float = 0.3) -> str:
        """分析图像"""
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                    {"type": "text", "text": question}
                ]
            }],
            temperature=temperature
        )

        return response.choices[0].message.content
