from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ClassCreate(BaseModel):
    class_name: str = Field(..., min_length=1)
    start_time: Optional[datetime] = None
    head_teacher_id: Optional[int] = Field(None, gt=0)


class ClassUpdate(BaseModel):
    class_name: Optional[str] = Field(None, min_length=1)
    start_time: Optional[datetime] = None
    head_teacher_id: Optional[int] = Field(None, gt=0)
