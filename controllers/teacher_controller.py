from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import TeacherService
from schemas.teacher import TeacheresUpdata
from schemas import ResponseBase, ListResponse

router = APIRouter(prefix="/teacher", tags=['老师管理模块'])


@router.post("/", response_model=ResponseBase, summary="新增老师")
def create_teacher(teacher: TeacheresUpdata, db: Session = Depends(get_db)):
    allowed_roles = ["counselor", "headteacher", "lecturer"]
    if teacher.role is not None and teacher.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="角色不合法！只能是 counselor / headteacher / lecturer"
        )
    data = TeacherService.create_teacher(db, teacher)
    return ResponseBase(data=data)


@router.get("/single", response_model=ResponseBase, summary="查询老师")
def get_teacher(
        db: Session = Depends(get_db),
        teacher_id: int = Query(None, description="按老师编号查询"),
        teacher_name: str = Query(None, description="按老师姓名查询"),
):
    teacher = TeacherService.get_teacher(db, teacher_id=teacher_id, teacher_name=teacher_name)
    if not teacher:
        raise HTTPException(status_code=404, detail="老师不存在")
    return ResponseBase(data=teacher)


@router.get("/all", response_model=ListResponse, summary="查询所有老师")
def get_all_teachers(db: Session = Depends(get_db)):
    data = TeacherService.get_all_teachers(db)
    return ListResponse(data=data, total=len(data))


@router.put("/{teacher_id}", response_model=ResponseBase, summary="修改老师信息")
def update_teacher(teacher_id: int, teacher: TeacheresUpdata, db: Session = Depends(get_db)):
    data = TeacherService.update_teacher(db, teacher_id, teacher)
    if not data:
        raise HTTPException(status_code=404, detail="老师不存在")
    return ResponseBase(data=data)


@router.delete("/{teacher_id}", response_model=ResponseBase, summary="删除老师")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    success = TeacherService.delete_teacher(db, teacher_id)
    if not success:
        raise HTTPException(status_code=404, detail="老师不存在或者已删除")
    return ResponseBase(message="删除成功", data=None)


@router.post("/bind-class", response_model=ResponseBase, summary="讲师绑定班级")
def bind_teacher_class(
        teacher_id: int = Query(..., description="讲师ID（必须传）"),
        class_ids: str = Query(..., description="班级ID列表，多个用英文逗号分隔，比如1,2,3"),
        db: Session = Depends(get_db)
):
    try:
        class_ids_list = [int(cid) for cid in class_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="班级ID必须是数字，多个用英文逗号分隔")

    teacher = TeacherService.bind_teacher_to_class(db, teacher_id, class_ids_list)
    if not teacher:
        raise HTTPException(status_code=400, detail="绑定失败：讲师不存在/不是讲师/班级不存在")

    return ResponseBase(
        code=200,
        message=f"讲师【{teacher.teacher_name}】绑定班级成功！",
        data={"teacher_id": teacher_id, "bind_class_ids": class_ids_list}
    )


@router.delete("/{teacher_id}/unbind-class/{class_id}", response_model=ResponseBase, summary="解除讲师-班级绑定")
def unbind_teacher_class(
        teacher_id: int,
        class_id: int,
        db: Session = Depends(get_db)
):
    success = TeacherService.unbind_teacher_from_class(db, teacher_id, class_id)
    if not success:
        raise HTTPException(status_code=400, detail="解除失败：讲师/班级不存在或未绑定")
    return ResponseBase(message="解除绑定成功")


@router.get("/{teacher_id}/head_classes", response_model=ResponseBase, summary="查班主任所带的班级")
def get_head_classes(teacher_id: int, db: Session = Depends(get_db)):
    data = TeacherService.get_head_classes(db, teacher_id)
    if isinstance(data, str):
        if data == "老师不存在":
            raise HTTPException(status_code=404, detail=data)
        else:
            raise HTTPException(status_code=400, detail=data)
    return ResponseBase(data=data)


@router.get("/{teacher_id}/teach_classes", response_model=ResponseBase, summary="查讲师所教的班级")
def get_teach_classes(teacher_id: int, db: Session = Depends(get_db)):
    data = TeacherService.get_teach_classes(db, teacher_id)
    if isinstance(data, str):
        if data == "老师不存在":
            raise HTTPException(status_code=404, detail=data)
        else:
            raise HTTPException(status_code=400, detail=data)
    return ResponseBase(data=data)


@router.get("/{teacher_id}/my_students", response_model=ResponseBase, summary="查顾问带的学生")
def get_my_students(teacher_id: int, db: Session = Depends(get_db)):
    data = TeacherService.get_my_students(db, teacher_id)
    if isinstance(data, str):
        if data == "老师不存在":
            raise HTTPException(status_code=404, detail=data)
        else:
            raise HTTPException(status_code=400, detail=data)
    return ResponseBase(data=data)
