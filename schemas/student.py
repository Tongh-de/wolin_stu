from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    stu_name: str = Field(..., min_length=1, max_length=20)
    class_id: int = Field(..., gt=0)
    native_place: str = Field(..., max_length=50)
    graduated_school: str = Field(..., max_length=50)
    major: str = Field(..., max_length=50)
    admission_date: datetime
    graduation_date: datetime
    education: str = Field(..., max_length=20)
    advisor_id: Optional[int] = None
    age: int = Field(..., gt=0, lt=150)
    gender: str = Field(..., pattern="^(男|女)$")


class StudentUpdate(BaseModel):
    stu_name: Optional[str] = Field(None, max_length=20)
    class_id: Optional[int] = Field(None, gt=0)
    native_place: Optional[str] = Field(None, max_length=50)
    graduated_school: Optional[str] = Field(None, max_length=50)
    major: Optional[str] = Field(None, max_length=50)
    admission_date: Optional[datetime] = None
    graduation_date: Optional[datetime] = None
    education: Optional[str] = Field(None, max_length=20)
    advisor_id: Optional[int] = None
    age: Optional[int] = Field(None, gt=0, lt=150)
    gender: Optional[str] = Field(None, pattern="^(男|女)$")
