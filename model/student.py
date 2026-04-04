from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class StuBasicInfo(Base):
    __tablename__ = "stu_basic_info"
    stu_id = Column(Integer, primary_key=True, autoincrement=True)
    stu_name = Column(String(20), nullable=False)

    native_place = Column(String(50), nullable=False)
    graduated_school = Column(String(50), nullable=False)
    major = Column(String(50), nullable=False)
    admission_date = Column(DateTime, nullable=False)
    graduation_date = Column(DateTime, nullable=False)
    education = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(2), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=True)

    advisor_id = Column(Integer, ForeignKey("teacher.teacher_id"))
    class_id = Column(Integer, ForeignKey("class.class_id"), nullable=False)

    class_ = relationship("Class", back_populates="students")
    counselor = relationship("Teacher", foreign_keys=[advisor_id], back_populates="students")
