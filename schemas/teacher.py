from pydantic import BaseModel, Field
from typing import Optional


class TeacheresUpdata(BaseModel):
    teacher_name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
