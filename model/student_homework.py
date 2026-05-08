"""
学生作业/作文模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from database import Base


class StudentHomework(Base):
    """学生作业/作文表"""
    __tablename__ = "student_homework"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(32), nullable=False, index=True, comment="学生ID")
    title = Column(String(200), nullable=True, comment="作业标题")
    content = Column(Text, nullable=False, comment="作业内容")
    homework_type = Column(String(32), default="composition", comment="类型: composition=作文, reading=阅读笔记, etc")
    status = Column(String(16), default="pending", comment="状态: pending=待点评, reviewed=已点评")
    review_comment = Column(Text, nullable=True, comment="点评内容")
    reviewed_at = Column(DateTime, nullable=True, comment="点评时间")
    created_at = Column(DateTime, server_default=func.now(), comment="提交时间")
    file_path = Column(String(500), nullable=True, comment="作业文件路径")
    original_filename = Column(String(255), nullable=True, comment="原始文件名")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "title": self.title,
            "content": self.content,
            "homework_type": self.homework_type,
            "status": self.status,
            "review_comment": self.review_comment,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "file_path": self.file_path,
            "original_filename": self.original_filename
        }
