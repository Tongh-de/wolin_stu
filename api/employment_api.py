# 导入FastAPI相关工具
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

# 数据库连接
from database import get_db

# 导入你的DAO方法
from dao.employment_dao import (
    query_employment,
    update_employment,
    delete_employment
)

# 创建路由
router = APIRouter(prefix="/employment", tags=["就业信息模块"])

# ------------------------------
# 修改就业信息的数据格式
# ------------------------------
class EmploymentUpdate(BaseModel):
    stu_id: int =None
    stu_name: str  = None
    open_time: date = None
    offer_time: date  = None
    company: str  = None
    salary: float  = None

# ------------------------------
# 1. 多条件查询（所有查询都走这里）
# ------------------------------
@router.get("/query")
def query_employment_api(
    emp_id: int = Query(None, description="就业编号"),
    stu_id: int = Query(None, description="学生编号"),
    stu_name: str = Query(None, description="学生姓名"),
    company: str = Query(None, description="公司名称"),
    min_salary: float = Query(None, description="最低工资"),
    max_salary: float = Query(None, description="最高工资"),
    skip: int = Query(0, description="跳过几条"),
    limit: int = Query(50, description="每页几条"),
    db: Session = Depends(get_db)
):
    data = query_employment(
        db=db,
        emp_id=emp_id,
        stu_id=stu_id,
        stu_name=stu_name,
        company=company,
        min_salary=min_salary,
        max_salary=max_salary,
        skip=skip,
        limit=limit
    )
    if not data:
        return {
            "code": 200,
            "msg": "未查询到符合条件的就业信息",
            "data": []
        }
    return {
        "code": 200,
        "msg": "查询成功",
        "data": data
    }

# ------------------------------
# 2. 修改就业信息（调用 DAO，不是 API 自身）
# ------------------------------
@router.put("/update/{emp_id}")
def update_employment_api(
    emp_id: int,
    update_data: EmploymentUpdate,
    db: Session = Depends(get_db)
):
    # ✅ 正确写法：调用 DAO，不是调用接口函数
    employment = query_employment(
        db=db,
        emp_id=emp_id,
        limit=1
    )

    if not employment:
        return {"code": 404, "msg": "就业信息不存在"}

    employment = employment[0]

    success = update_employment(db, employment, update_data)
    if success:
        return {"code": 200, "msg": "修改成功"}
    else:
        return {"code": 500, "msg": "修改失败"}

# ------------------------------
# 3. 逻辑删除（调用 DAO）
# ------------------------------
@router.delete("/delete/{emp_id}")
def delete_employment_api(
    emp_id: int,
    db: Session = Depends(get_db)
):
    # ✅ 正确写法：调用 DAO
    employment = query_employment(
        db=db,
        emp_id=emp_id,
        limit=1
    )

    if not employment:
        return {"code": 404, "msg": "信息不存在或已删除"}

    employment = employment[0]

    success = delete_employment(db, employment)
    if success:
        return {"code": 200, "msg": "删除成功"}
    else:
        return {"code": 500, "msg": "删除失败"}