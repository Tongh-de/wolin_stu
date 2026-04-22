from pydantic import BaseModel
from typing import Optional, List, Any

class Text2SQLRequest(BaseModel):
    """Text2SQL 请求模型"""
    question: str  # 自然语言问题
    session_id: Optional[str] = None  # 会话ID，用于多轮对话
    include_schema: bool = True  # 是否包含表结构上下文
    limit: Optional[int] = 100  # 结果限制

class Text2SQLResponse(BaseModel):
    """Text2SQL 响应模型"""
    sql: str  # 生成的SQL语句
    data: Optional[List[dict]] = None  # 查询结果
    count: int = 0  # 结果数量
    message: str = ""  # 消息提示
    session_id: str  # 会话ID

class SQLExplainRequest(BaseModel):
    """SQL解释请求"""
    sql: str

class SQLExplainResponse(BaseModel):
    """SQL解释响应"""
    sql: str
    explanation: str  # SQL解释

class SQLValidateRequest(BaseModel):
    """SQL验证请求"""
    sql: str

class SQLValidateResponse(BaseModel):
    """SQL验证响应"""
    valid: bool
    message: str
    sql: str
