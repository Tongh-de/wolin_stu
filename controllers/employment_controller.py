from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from services import EmploymentService
from schemas import ResponseBase, ListResponse
from schemas.emp_schemas import EmploymentUpdate, EmploymentResp, EmploymentCreate
from utils.auth_deps import get_current_user, require_admin, require_teacher_or_admin
from model.user import User
from model.employment import Employment

router = APIRouter(prefix="/employment", tags=["就业管理模块"])


@router.get("/list", response_model=ListResponse)
def get_employment_list(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_teacher_or_admin)  # 教师或管理员
):
    """获取所有就业信息列表"""
    data = EmploymentService.get_all_employments(db)
    list_data = [EmploymentResp.model_validate(item) for item in data]
    return ListResponse(code=200, message="查询成功", data=list_data, total=len(list_data))


@router.post("/", response_model=ResponseBase)
def create_employment(
        create_data: EmploymentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_teacher_or_admin)  # 教师或管理员
):
    """创建就业信息"""
    # 检查该学生是否已有就业记录
    existing = EmploymentService.get_employment_by_stu_id(db, create_data.stu_id)
    if existing:
        raise HTTPException(status_code=400, detail="该学生已有就业记录")

    emp = EmploymentService.create_employment(db, create_data)
    if not emp:
        raise HTTPException(status_code=500, detail="创建失败")

    emp_data = EmploymentResp.model_validate(emp)
    return ResponseBase(code=200, message="创建成功", data=emp_data)


@router.get("/students/{stu_id}", response_model=ResponseBase)
def get_student_employment(
        stu_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # 登录用户
):
    # 学生只能查自己的就业信息
    if current_user.role == 'student' and current_user.student_id != stu_id:
        raise HTTPException(status_code=403, detail="只能查询自己的就业信息")
    
    emp = EmploymentService.get_employment_by_stu_id(db, stu_id)
    if not emp:
        raise HTTPException(status_code=404, detail="未找到就业信息")
    emp_data = EmploymentResp.model_validate(emp)
    return ResponseBase(code=200, message="查询成功", data=emp_data)


@router.get("/class/{class_id}", response_model=ListResponse)
def get_class_employment(
        class_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_teacher_or_admin)  # 教师或管理员
):
    data = EmploymentService.get_employment_by_class_id(db, class_id)
    list_data = [EmploymentResp.model_validate(item) for item in data]
    return ListResponse(code=200, message="查询成功", data=list_data, total=len(list_data))


@router.get("/query", response_model=ListResponse)
def query_employment(
    stu_id: int | None = Query(default=None, description="学生ID"),
    company: str | None = Query(default=None, description="公司名称"),
    min_salary: int | None = Query(default=None, description="最低薪资"),
    max_salary: int | None = Query(default=None, description="最高薪资"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 登录用户
):
    # 学生只能查自己的
    if current_user.role == 'student' and current_user.student_id:
        stu_id = current_user.student_id
    
    data = EmploymentService.query_employment(db, stu_id=stu_id, company=company, min_salary=min_salary, max_salary=max_salary)
    list_data = [EmploymentResp.model_validate(item) for item in data]
    return ListResponse(code=200, message="查询成功", data=list_data, total=len(list_data))


@router.put("/students/{stu_id}", response_model=ResponseBase)
def update_student_employment(
        stu_id: int,
        update_data: EmploymentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_teacher_or_admin)  # 教师或管理员
):
    emp = EmploymentService.get_employment_by_stu_id(db, stu_id)
    if not emp:
        raise HTTPException(status_code=404, detail="就业记录不存在")

    updated_emp = EmploymentService.update_employment(db, emp, update_data)
    if not updated_emp:
        raise HTTPException(status_code=500, detail="更新失败")

    updated_data = EmploymentResp.model_validate(updated_emp)
    return ResponseBase(code=200, message="更新成功", data=updated_data)


@router.delete("/delete/{emp_id}", response_model=ResponseBase)
def delete_employment_api(
        emp_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    emp = EmploymentService.get_employment_by_emp_id(db, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="记录不存在或已删除")

    success = EmploymentService.delete_employment(db, emp)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")

    return ResponseBase(code=200, message="删除成功", data=None)


@router.put("/restore/{emp_id}", response_model=ResponseBase)
def restore_emp(
        emp_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    success = EmploymentService.restore_employment(db, emp_id)
    if not success:
        raise HTTPException(status_code=404, detail="恢复失败")
    return ResponseBase(code=200, message="恢复成功", data=None)
