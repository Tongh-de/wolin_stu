"""
应用配置管理
统一管理所有硬编码的配置项
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置 - 必须从环境变量读取
    DATABASE_URL: str = ""
    
    # JWT配置 - 必须从环境变量读取
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 模型配置验证
    @property
    def MODEL_CONFIGS(self) -> dict:
        return {
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat"
            },
            "kimi": {
                "api_key": os.getenv("KIMI_API_KEY", ""),
                "base_url": "https://api.moonshot.cn/v1",
                "model": "moonshot-v1-8k"
            },
            "qwen": {
                "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-plus"
            },
            "gpt4": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4"
            }
        }
    
    @property
    def DEFAULT_TEMPERATURE(self) -> float:
        return float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    
    @property
    def DEFAULT_MAX_TOKENS(self) -> int:
        return int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
    INTENT_THRESHOLD: float = 0.6
    MAX_SAMPLE_COUNT: int = 10
    RAG_SIMILARITY_THRESHOLD: float = 1.5
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:8099",
        "http://127.0.0.1:8099",
        "http://localhost:3000"
    ]
    
    # 服务配置
    HOST: str = "127.0.0.1"
    PORT: int = 8099
    
    # 上传配置
    UPLOAD_DIR: str = "uploads/homework"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    SUPPORTED_EXTENSIONS: List[str] = ['txt', 'pdf', 'docx']
    
    # AI参数配置（从环境变量读取）
    INTENT_THRESHOLD: float = 0.6
    MAX_SAMPLE_COUNT: int = 10
    RAG_SIMILARITY_THRESHOLD: float = 1.5
    
    class Config:
        env_file = ".env"
        extra = "allow"  # 允许额外字段


# 全局配置实例
settings = Settings()

# 安全检查：确保关键配置已设置
def validate_settings():
    errors = []
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL")
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY")
    elif len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY (长度必须 >= 32)")
    
    if errors:
        raise ValueError(f"缺少必要的环境变量: {', '.join(errors)}")

validate_settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
