from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dao import teacher_dao as dao

router = APIRouter(
    prefix="/teacher",
    tags=['老师管理模块']
)

@router.post("/")
def create_teacher(teacher: dao.TeacheresUpdata, db: Session = Depends(get_db)):
    return dao.create_teacher(db, teacher)

@router.get("/{teacher_id}")
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    t = dao.get_teacher(db, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="老师不存在")
    return t

@router.get("/")
def get_all_teachers(db: Session = Depends(get_db)):
    return dao.get_all_teachers(db)

@router.put("/{teacher_id}")
def update_teacher(teacher_id: int, teacher: dao.TeacheresUpdata, db: Session = Depends(get_db)):
    return dao.update_teacher(db, teacher_id, teacher)

@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    return dao.delete_teacher(db, teacher_id)

# ===================== 3大关联查询接口 =====================
# 1. 授课老师教哪些班
@router.get("/{teacher_id}/teach-classes")
def get_teach_classes(teacher_id: int, db: Session = Depends(get_db)):
    return {"teacher_id": teacher_id, "teach_classes": dao.get_teach_classes(db, teacher_id)}

# 2. 班主任带哪些班
@router.get("/{teacher_id}/head-classes")
def get_head_classes(teacher_id: int, db: Session = Depends(get_db)):
    return {"teacher_id": teacher_id, "head_classes": dao.get_headteacher_classes(db, teacher_id)}

# 3. 销售顾问负责哪些学生
@router.get("/{teacher_id}/sale-students")
def get_sales_students(teacher_id: int, db: Session = Depends(get_db)):
    return {"teacher_id": teacher_id, "sale_students": dao.get_sales_students(db, teacher_id)}
