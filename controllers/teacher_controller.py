from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import TeacherService
from schemas.teacher import TeacherUpdate
from schemas import ResponseBase, ListResponse
from utils.logger import get_logger
from utils.auth_deps import get_current_user, require_admin, require_teacher_or_admin
from model.user import User

logger = get_logger("teacher")
router = APIRouter(prefix="/teacher", tags=['老师管理模块'])


@router.post("/", response_model=ResponseBase, summary="新增老师")
def create_teacher(
        teacher: TeacherUpdate, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"新增教师: {teacher.teacher_name}, 角色: {teacher.role}, 操作者: {current_user.username}")
    allowed_roles = ["counselor", "headteacher", "lecturer"]
    if teacher.role is not None and teacher.role not in allowed_roles:
        logger.warning(f"角色不合法: {teacher.role}")
        raise HTTPException(
            status_code=400,
            detail="角色不合法！只能是 counselor / headteacher / lecturer"
        )
    data = TeacherService.create_teacher(db, teacher)
    logger.info(f"教师创建成功: teacher_id={data['teacher_id']}")
    return ResponseBase(data=data)


@router.get("/single", response_model=ResponseBase, summary="查询老师")
def get_teacher(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),  # 登录用户
        teacher_id: int = Query(None, description="按老师编号查询"),
        teacher_name: str = Query(None, description="按老师姓名查询"),
):
    logger.info(f"查询教师: teacher_id={teacher_id}, teacher_name={teacher_name}, 操作者: {current_user.username}")
    teacher = TeacherService.get_teacher(db, teacher_id=teacher_id, teacher_name=teacher_name)
    if not teacher:
        logger.warning(f"教师不存在: teacher_id={teacher_id}, teacher_name={teacher_name}")
        raise HTTPException(status_code=404, detail="老师不存在")
    logger.info(f"查询成功: {teacher['teacher_name']}")
    return ResponseBase(data=teacher)


@router.get("/all", response_model=ListResponse, summary="查询所有老师")
def get_all_teachers(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # 登录用户
):
    logger.info(f"查询所有教师, 操作者: {current_user.username}")
    data = TeacherService.get_all_teachers(db)
    logger.info(f"查询成功: 共{len(data)}位教师")
    return ListResponse(data=data, total=len(data))


@router.put("/{teacher_id}", response_model=ResponseBase, summary="修改老师信息")
def update_teacher(
        teacher_id: int, 
        teacher: TeacherUpdate, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"更新教师: teacher_id={teacher_id}, 操作者: {current_user.username}")
    data = TeacherService.update_teacher(db, teacher_id, teacher)
    if not data:
        logger.warning(f"教师不存在: teacher_id={teacher_id}")
        raise HTTPException(status_code=404, detail="老师不存在")
    logger.info(f"教师更新成功: teacher_id={teacher_id}")
    return ResponseBase(data=data)


@router.delete("/{teacher_id}", response_model=ResponseBase, summary="删除老师")
def delete_teacher(
        teacher_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # 仅管理员
):
    logger.info(f"删除教师: teacher_id={teacher_id}, 操作者: {current_user.username}")
    success = TeacherService.delete_teacher(db, teacher_id)
    if not success:
        logger.warning(f"教师不存在: teacher_id={teacher_id}")
        raise HTTPException(status_code=404, detail="老师不存在或者已删除")
    logger.info(f"教师删除成功: teacher_id={teacher_id}")
    return ResponseBase(message="删除成功", data=None)


@router.post("/bind-class", response_model=ResponseBase, summary="讲师绑定班级")
def bind_teacher_class(
        teacher_id: int = Query(..., description="讲师ID（必须传）"),
        class_ids: str = Query(..., description="班级ID列表，多个用英文逗号分隔，比如1,2,3"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_teacher_or_admin)  # 教师或管理员
):
    logger.info(f"绑定班级: teacher_id={teacher_id}, class_ids={class_ids}, 操作者: {current_user.username}")
    try:
        class_ids_list = [int(cid) for cid in class_ids.split(",")]
    except ValueError:
        logger.warning(f"班级ID格式错误: {class_ids}")
        raise HTTPException(status_code=400, detail="班级ID必须是数字，多个用英文逗号分隔")

    teacher = TeacherService.bind_teacher_to_class(db, teacher_id, class_ids_list)
    if not teacher:
        logger.warning(f"绑定失败: teacher_id={teacher_id}")
        raise HTTPException(status_code=400, detail="绑定失败：讲师不存在/不是讲师/班级不存在")

    logger.info(f"绑定成功: teacher_id={teacher_id}, class_ids={class_ids_list}")
    return ResponseBase(
        code=200,
        message=f"讲师【{teacher.teacher_name}】绑定班级成功！",
        data={"teacher_id": teacher_id, "bind_class_ids": class_ids_list}
    )


@router.delete("/{teacher_id}/unbind-class/{class_id}", response_model=ResponseBase, summary="解除讲师-班级绑定")
def unbind_teacher_class(
        teacher_id: int,
        class_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_teacher_or_admin)  # 教师或管理员
):
    logger.info(f"解除绑定: teacher_id={teacher_id}, class_id={class_id}, 操作者: {current_user.username}")
    success = TeacherService.unbind_teacher_from_class(db, teacher_id, class_id)
    if not success:
        logger.warning(f"解除绑定失败: teacher_id={teacher_id}, class_id={class_id}")
        raise HTTPException(status_code=400, detail="解除失败：讲师/班级不存在或未绑定")
    logger.info(f"解除绑定成功")
    return ResponseBase(message="解除绑定成功")


@router.get("/{teacher_id}/head_classes", response_model=ResponseBase, summary="查班主任所带的班级")
def get_head_classes(
        teacher_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # 登录用户
):
    logger.info(f"查询班主任所带班级: teacher_id={teacher_id}, 操作者: {current_user.username}")
    data = TeacherService.get_head_classes(db, teacher_id)
    if isinstance(data, str):
        logger.warning(f"查询失败: {data}")
        if data == "老师不存在":
            raise HTTPException(status_code=404, detail=data)
        else:
            raise HTTPException(status_code=400, detail=data)
    logger.info(f"查询成功: 共{len(data)}个班级")
    return ResponseBase(data=data)


@router.get("/{teacher_id}/teach_classes", response_model=ResponseBase, summary="查讲师所教的班级")
def get_teach_classes(
        teacher_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # 登录用户
):
    logger.info(f"查询讲师所教班级: teacher_id={teacher_id}, 操作者: {current_user.username}")
    data = TeacherService.get_teach_classes(db, teacher_id)
    if isinstance(data, str):
        logger.warning(f"查询失败: {data}")
        if data == "老师不存在":
            raise HTTPException(status_code=404, detail=data)
        else:
            raise HTTPException(status_code=400, detail=data)
    logger.info(f"查询成功: 共{len(data)}个班级")
    return ResponseBase(data=data)


@router.get("/{teacher_id}/my_students", response_model=ResponseBase, summary="查顾问带的学生")
def get_my_students(
        teacher_id: int, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # 登录用户
):
    logger.info(f"查询顾问所带学生: teacher_id={teacher_id}, 操作者: {current_user.username}")
    data = TeacherService.get_my_students(db, teacher_id)
    if isinstance(data, str):
        logger.warning(f"查询失败: {data}")
        if data == "老师不存在":
            raise HTTPException(status_code=404, detail=data)
        else:
            raise HTTPException(status_code=400, detail=data)
    logger.info(f"查询成功: 共{len(data)}名学生")
    return ResponseBase(data=data)
