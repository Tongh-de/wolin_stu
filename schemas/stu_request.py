from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime

class NewStudentData(BaseModel):
    stu_name: Optional[str] = None
    class_id: Optional[int] = None
    native_place: Optional[str] = None
    graduated_school: Optional[str] = None
    major: Optional[str] = None
    admission_date: Optional[datetime] = None
    graduation_date: Optional[datetime] = None
    education: Optional[str] = None
    advisor_id: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None



