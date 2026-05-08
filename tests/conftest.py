"""
pytest 配置
"""
import sys
import os

# 确保项目根目录在 Python 路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
