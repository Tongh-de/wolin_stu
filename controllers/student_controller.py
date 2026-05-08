from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services import StudentService, EmploymentService
from schemas.student import StudentCreate, StudentUpdate
from schemas import ResponseBase, ListResponse
from typing import Optional
from utils.logger import get_logger
from utils.auth_deps import get_current_user, require_admin
from model.user import User

logger = get_logger("student")
router = APIRouter(prefix="/students", tags=["学生管理"])


@router.post("/", response_model=ResponseBase)
def create_student(
        new_student_data: StudentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员可创建
):
    logger.info(f"新增学生: {new_student_data.stu_name}, 班级ID: {new_student_data.class_id}, 操作者: {current_user.username}")
    new_student = StudentService.create_student(new_student_data, db)
    # 级联创建就业信息
    EmploymentService.create_empty_employment(db, new_student['stu_id'], new_student['stu_name'], new_student['class_id'])
    logger.info(f"学生创建成功: stu_id={new_student['stu_id']}")
    return ResponseBase(data=new_student)


@router.get("/", response_model=ListResponse)
def get_students(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),  # 登录即可访问，权限在函数内判断
        stu_id: Optional[int] = Query(None, description="按学生编号查询"),
        stu_name: Optional[str] = Query(None, description="按学生姓名查询"),
        class_id: Optional[int] = Query(None, description="按班级编号查询")
):
    logger.info(f"查询学生列表: stu_id={stu_id}, stu_name={stu_name}, class_id={class_id}, 操作者: {current_user.username}")
    
    # 学生只能查自己的信息
    if current_user.role == 'student' and current_user.student_id:
        students = StudentService.get_students(db, stu_id=current_user.student_id)
    else:
        students = StudentService.get_students(db, stu_id=stu_id, stu_name=stu_name, class_id=class_id)
    
    logger.info(f"查询成功: 共{len(students)}条记录")
    return ListResponse(data=students, total=len(students))


@router.put("/{stu_id}", response_model=ResponseBase)
def update_student(
        stu_id: int,
        update_data: StudentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员可更新
):
    logger.info(f"更新学生: stu_id={stu_id}, 操作者: {current_user.username}")
    is_update_student = StudentService.update_student(db, stu_id, update_data)
    if not is_update_student:
        logger.warning(f"学生不存在: stu_id={stu_id}")
        raise HTTPException(status_code=400, detail="没有这个学生")
    logger.info(f"学生更新成功: stu_id={stu_id}")
    return ResponseBase(data=is_update_student)


@router.delete("/{stu_id}", response_model=ResponseBase)
def delete_student(
        stu_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员可删除
):
    logger.info(f"删除学生: stu_id={stu_id}, 操作者: {current_user.username}")
    is_delete_student = StudentService.delete_student(db, stu_id)
    if is_delete_student == '不存在这个学生或已被删除':
        logger.warning(f"学生不存在: stu_id={stu_id}")
        raise HTTPException(status_code=400, detail="没有这个学生或已被删除")
    logger.info(f"学生删除成功: stu_id={stu_id}")
    return ResponseBase(message=is_delete_student, data=None)
