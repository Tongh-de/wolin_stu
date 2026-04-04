from sqlalchemy import Column, String, Integer, Date, Float, ForeignKey
from database import Base


class Employment(Base):
    __tablename__ = "employment"
    emp_id = Column(Integer, primary_key=True, autoincrement=True)
    stu_id = Column(
        Integer,
        ForeignKey("stu_basic_info.stu_id", ondelete="CASCADE"),
        nullable=False,
        comment="学生ID（外键关联学生表")
    stu_name = Column(String(20), nullable=False)
    open_time = Column(Date, comment="就业开放时间")
    offer_time = Column(Date, comment="offer下发时间")
    company = Column(String(50), comment="就业公司名称")
    salary = Column(Float, comment="就业薪资")
    is_deleted = Column(Integer, default=0)
