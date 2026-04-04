from pydantic import BaseModel
from typing import Optional
from datetime import date

class ExamData(BaseModel):
    stu_id: Optional[int] = None
    seq_no: Optional[int] = None
    grade: Optional[int] = None
    exam_date: Optional[date] = None
    is_deleted: Optional[int] = None
