from sqlalchemy.orm import Session
from model.teachers import Teacher
from model.teachers import TeacheresUpdata


# 新增老师
def create_teacher(db: Session, teacher: TeacheresUpdata):
    db_teacher = Teacher(**teacher.dict())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


# 查询单个老师
def get_teacher(db: Session, teacher_id: int):
    return db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()


# 查询所有老师
def get_all_teachers(db: Session):
    return db.query(Teacher).all()


# 修改老师
def update_teacher(db: Session, teacher_id: int, teacher: TeacheresUpdata):
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    for key, value in teacher.items():
        setattr(db_teacher, key, value)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


# 修改老师
def delete_teacher(db: Session, teacher_id: int):
    db_teacher = get_teacher(db, teacher_id)
    if db_teacher:
        db.delete(db_teacher)
        db.commit()
    return db_teacher


# ===================== 3 大关联查询 =====================
# 1. 授课老师教哪些班
# 1. 授课老师教哪些班
def get_teach_classes(db: Session, teacher_id: int):
    teacher = get_teacher(db, teacher_id)
    return teacher.teach_classes if teacher else []


# 2. 班主任带哪些班
def get_headteacher_classes(db: Session, teacher_id: int):
    teacher = get_teacher(db, teacher_id)
    return teacher.head_classes if teacher else []


# 3. 销售顾问负责哪些学生
def get_sales_students(db: Session, teacher_id: int):
    teacher = get_teacher(db, teacher_id)
    return teacher.sale_students if teacher else []
