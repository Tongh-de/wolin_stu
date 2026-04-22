from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class NewExamData(BaseModel):
    stu_id: int
    seq_no: int
    grade: int = Field(default=0, ge=0, le=100)
    exam_date: Optional[date] = None


class UpdateExamData(BaseModel):
    grade: int = Field(default=0, ge=0, le=100)
    exam_date: Optional[date] = None
