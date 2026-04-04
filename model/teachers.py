from sqlalchemy import ForeignKey, Table, Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from model.class_model import class_teacher


# 响应模型
class TeacheresUpdata(BaseModel):
    name: str
    role: str


# class_teachers = Table(
#     'class_teachers_association',
#     Base.metadata,
#     Column('class_id', Integer, ForeignKey('class_id'), primary_key=True),
#     Column('teacher_id', Integer, ForeignKey('teacher_id'), primary_key=True)
# )


class Teacher(Base):
    __tablename__ = "teacher"
    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_name = Column(String(30), comment="姓名")
    role = Column(String(20), comment="角色：counselor顾问/headteacher班主任/lecturer讲师")

    # 关联中间表(多对多)class.teacher()
    teach_classes = relationship('Class', secondary=class_teacher, back_populates='teachers')
    # 关联班主任(一对多)
    # head_classes = relationship('Class', foreign_keys='headteacher_id', back_populates='headteacher')
    # 关联学生表(一对多)
    students = relationship('StuBasicInfo', foreign_keys='StuBasicInfo.advisor_id', back_populates='counselor')
