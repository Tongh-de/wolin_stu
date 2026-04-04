from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# ------------------------------
# 班级基础 schema
# ------------------------------
class ClassBase(BaseModel):
    class_name: str
    start_time: datetime

# ------------------------------
# 创建班级（前端传参）
# ------------------------------
class ClassCreate(ClassBase):
    pass

# ------------------------------
# 更新班级（可选字段）
# ------------------------------
class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    start_time: Optional[datetime] = None

# ------------------------------
# 返回给前端的完整班级数据
# ------------------------------
class ClassOut(ClassBase):
    class_id: int

    class Config:
        from_attributes = True  # 关键：让Pydantic支持SQLAlchemy模型