from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 角色：admin=管理员, teacher=教师, student=学生
    role = Column(String(20), default="student", nullable=False)
    
    # 关联的学生ID（学生用户绑定）
    student_id = Column(Integer, ForeignKey("stu_basic_info.stu_id"), nullable=True)
    
    # 关联的教师ID（教师用户绑定）
    teacher_id = Column(Integer, ForeignKey("teacher.teacher_id"), nullable=True)