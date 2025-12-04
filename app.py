#!/usr/bin/env python3
"""
SciResearcher - 魔搭创空间入口文件
这是创空间默认的启动入口
"""

from gradio_app import create_interface

if __name__ == "__main__":
    # 创建并启动应用
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,  # 创空间需要公开分享
        show_error=True,
        inbrowser=False  # 创空间不需要自动打开浏览器
    )
