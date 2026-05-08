"""
应用配置管理
统一管理所有硬编码的配置项
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost/wolin"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 服务配置
    HOST: str = "127.0.0.1"
    PORT: int = 8099
    
    # 上传配置
    UPLOAD_DIR: str = "uploads/homework"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    SUPPORTED_EXTENSIONS: List[str] = ['txt', 'pdf', 'docx']
    
    # AI模型配置
    MODEL_CONFIGS = {
        "deepseek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "kimi": {
            "api_key": "",
            "base_url": "https://api.moonshot.cn/v1",
            "model": "moonshot-v1-8k"
        },
        "qwen": {
            "api_key": "",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus"
        },
        "gpt4": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4"
        }
    }
    
    # AI参数配置
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2048
    INTENT_THRESHOLD: float = 0.6
    MAX_SAMPLE_COUNT: int = 10
    RAG_SIMILARITY_THRESHOLD: float = 1.5
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:8099",
        "http://127.0.0.1:8099",
        "http://localhost:3000"
    ]
    
    class Config:
        env_file = ".env"
        extra = "allow"  # 允许额外字段


# 全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
