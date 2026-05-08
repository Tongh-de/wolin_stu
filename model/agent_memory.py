"""
Agent 对话记忆模型
用于存储 agent 的会话历史
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from database import Base


class AgentMemory(Base):
    """Agent 会话记忆表"""
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True, comment="会话ID")
    user_id = Column(Integer, nullable=True, index=True, comment="用户ID，与users表关联")
    role = Column(String(16), nullable=False, comment="角色: user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    intent = Column(String(32), nullable=True, comment="该消息的意图类型")
    model_used = Column(String(64), nullable=True, comment="使用的模型")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content
        }
